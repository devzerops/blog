import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from markupsafe import Markup
from config import Config
from app.database import db
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
import datetime
import re

# 서비스 레이어 임포트
from app.services import (
    PostService,
    UserService,
    CategoryService,
    MediaService
)
from app.utils import file_utils

migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

# 서비스 레이어 인스턴스 생성
post_service = PostService()
user_service = UserService()
category_service = CategoryService()
media_service = MediaService()

# 유틸리티 인스턴스
file_util = file_utils

def strip_images_filter(html_content):
    if html_content is None:
        return ''
    cleaned_content = re.sub(r'<img(?:\s[^>]*)?>', '', str(html_content), flags=re.IGNORECASE)
    return cleaned_content

def nl2br_filter(s):
    if s is None:
        return ''
    return Markup(str(s).replace('\n', '<br>\n'))

def mask_ip_filter(ip_address_str):
    if not ip_address_str: # Handle None or empty string
        return "N/A"
    parts = ip_address_str.split('.')
    if len(parts) == 4: # IPv4
        return f"{parts[0]}.{parts[1]}.X.X"
    elif ':' in ip_address_str: # IPv6 (very basic check, just mask it generally)
        # For simplicity, just return a generic mask for IPv6 or identify it.
        # A more robust IPv6 masking might be complex.
        return "IPv6 Address"
    return "Invalid IP" # Fallback for unexpected format

def create_app(config_class=Config):
    # 로깅 설정
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # Flask 애플리케이션 초기화
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class())
    
    # 로깅 설정 - 기본 로그 레벨 설정
    app.logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    
    # 로그 포맷 설정 (CLF - Common Log Format)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    app.logger.addHandler(console_handler)
    
    # 서드파티 로거 레벨 설정 (에러만 표시)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('PIL').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('markdown').setLevel(logging.ERROR)
    
    # HTTP 요청/응답 로깅 미들웨어
    @app.after_request
    def log_request(response):
        # 정적 파일 요청은 로깅에서 제외
        if request.path.startswith('/static/'):
            return response
            
        # 로그 메시지 구성
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string.split(' ')[0] if request.user_agent else 'Unknown',  # 브라우저/클라이언트 정보만 추출
            'response_size': None
        }
        
        # 스트리밍 응답이 아닌 경우에만 응답 크기 기록
        if not response.direct_passthrough:
            try:
                log_data['response_size'] = len(response.get_data())
            except Exception as e:
                app.logger.warning(f'Failed to get response size: {str(e)}')
        
        # 4xx, 5xx 에러인 경우 WARNING 레벨로 로깅
        if 400 <= response.status_code < 600:
            app.logger.warning('HTTP Request: %s', log_data)
        else:
            app.logger.info('HTTP Request: %s', log_data)
            
        return response
    
    # 애플리케이션 시작 로그
    app.logger.info('애플리케이션이 시작되었습니다.')
    
    # 확장 초기화
    bootstrap.init_app(app)
    
    # 서비스 인스턴스를 애플리케이션 컨텍스트에 등록
    @app.context_processor
    def inject_services():
        return {
            'post_service': post_service,
            'user_service': user_service,
            'category_service': category_service,
            'media_service': media_service
        }

    app.jinja_env.filters['strip_images'] = strip_images_filter
    app.jinja_env.filters['nl2br'] = nl2br_filter
    app.jinja_env.filters['mask_ip'] = mask_ip_filter

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    upload_folder = app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        upload_folder = os.path.join(app.root_path, 'static', 'uploads') 
        app.config['UPLOAD_FOLDER'] = upload_folder
        
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Error creating upload folder {upload_folder}: {e}")
        pass

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.routes_auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix='/auth')

    # Import from the new routes package structure
    from app.routes.admin import bp_admin
    app.register_blueprint(bp_admin)

    from app.routes_public import bp_public
    app.register_blueprint(bp_public) 

    # Import PageView model here to avoid circular import if it was at the top
    from app.models import PageView

    @app.after_request
    def log_page_view(response):
        # Avoid logging for static files or if the request had an error (e.g., 404 for static might still try to log)
        if request.path.startswith('/static') or response.status_code // 100 != 2:
            return response

        try:
            post_id = None
            # If we want to associate views with specific posts, 
            # we might need to access view_args if a post_id is part of the URL.
            # For example, if a view function for a post detail page is called, 
            # request.view_args might contain {'post_id': 123}
            # This part needs careful implementation based on how post_id is available.
            # For now, we'll leave post_id as None for general page views.

            page_view = PageView(
                path=request.path,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                post_id=post_id # This will be None for now
            )
            db.session.add(page_view)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Error logging page view: {e}")
            db.session.rollback() # Rollback in case of error
        return response

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.datetime.now(datetime.timezone.utc).year}

    @app.context_processor
    def inject_site_settings():
        from app.models import SiteSetting # Import here to avoid circular dependencies
        settings = SiteSetting.query.first()
        if settings:
            return {'site_settings': settings}
        # If no settings found, you might want to return defaults or an empty object
        # For now, let's return None, templates can check for existence
        # Or, return a default SiteSetting object if that's preferred, though the admin page creates one.
        return {'site_settings': None} # Or SiteSetting() if you want default values always present

    @app.cli.command('create-admin')
    def create_admin_command():
        """Creates the admin user."""
        from app.models import User
        
        if User.query.filter_by(username='admin').first():
            print('Admin user already exists.')
            return
        
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            default_pw = 'adminpass' 
            print(f'ADMIN_PASSWORD environment variable not set. Using default: {default_pw}')
            admin_password = default_pw
            
        admin = User(username='admin')
        admin.set_password(admin_password) 
        db.session.add(admin) 
        db.session.commit()
        print(f'Admin user created. Please ensure a strong password is used in production (set via ADMIN_PASSWORD env var).')

    return app
