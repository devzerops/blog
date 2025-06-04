import os
import logging
from flask import Flask, request
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from markupsafe import Markup

from config import config
from app.database import db
from app.utils.filters import register_template_filters
from app.utils.logging import setup_logging
from app.utils.context_processors import register_context_processors

# 확장 인스턴스
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""

    # 설정 환경 결정
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # Flask 애플리케이션 생성
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # 로깅 설정
    setup_logging(app)

    # 필요한 디렉토리 생성
    create_directories(app)

    # 확장 초기화
    initialize_extensions(app)

    # 템플릿 필터 등록
    register_template_filters(app)

    # 컨텍스트 프로세서 등록
    register_context_processors(app)

    # 블루프린트 등록
    register_blueprints(app)

    # CLI 명령 등록
    register_cli_commands(app)

    # 미들웨어 등록
    register_middleware(app)

    app.logger.info('애플리케이션이 시작되었습니다.')

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

    return app

def create_directories(app):
    """필요한 디렉토리 생성"""
    try:
        os.makedirs(app.instance_path, exist_ok=True)

        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(os.path.join(upload_folder, 'thumbnails'), exist_ok=True)

        temp_folder = app.config.get('TEMP_FOLDER')
        if temp_folder:
            os.makedirs(temp_folder, exist_ok=True)

    except OSError as e:
        app.logger.error(f"디렉토리 생성 오류: {e}")

def initialize_extensions(app):
    """Flask 확장 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.public import bp_public
    from app.routes.auth import bp_auth
    from app.routes.admin import bp_admin

    app.register_blueprint(bp_public)
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_admin, url_prefix='/admin')

def register_cli_commands(app):
    """CLI 명령 등록"""
    from app.cli import register_commands
    register_commands(app)

def register_middleware(app):
    """미들웨어 등록"""
    from app.middleware import register_middleware_handlers
    register_middleware_handlers(app)
```
I have detected missing codes. Incorporating codes.

```python
import os
import logging
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from markupsafe import Markup
import datetime
import re

from config import config
from app.database import db
from app.utils.filters import register_template_filters, strip_images_filter, nl2br_filter, mask_ip_filter
from app.utils.logging import setup_logging
from app.utils.context_processors import register_context_processors
from app.utils import file_utils

# 서비스 레이어 임포트
from app.services import (
    PostService,
    UserService,
    CategoryService,
    MediaService
)

# 서비스 레이어 인스턴스 생성
post_service = PostService()
user_service = UserService()
category_service = CategoryService()
media_service = MediaService()

# 유틸리티 인스턴스
file_util = file_utils

# 확장 인스턴스
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""

    # 설정 환경 결정
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # Flask 애플리케이션 생성
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # 로깅 설정
    setup_logging(app)

    # 필요한 디렉토리 생성
    create_directories(app)

    # 확장 초기화
    initialize_extensions(app)

    # 템플릿 필터 등록
    register_template_filters(app)

    # 컨텍스트 프로세서 등록
    register_context_processors(app)

    # 블루프린트 등록
    register_blueprints(app)

    # CLI 명령 등록
    register_cli_commands(app)

    # 미들웨어 등록
    register_middleware(app)

    # 서비스 인스턴스를 애플리케이션 컨텍스트에 등록
    @app.context_processor
    def inject_services():
        return {
            'post_service': post_service,
            'user_service': user_service,
            'category_service': category_service,
            'media_service': media_service
        }
    
    app.logger.info('애플리케이션이 시작되었습니다.')

    # Import PageView model here to avoid circular import if it was at the top
    from app.models import PageView, SiteSetting

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
        settings = SiteSetting.query.first()
        if settings:
            return {'site_settings': settings}
        # If no settings found, you might want to return defaults or an empty object
        # For now, let's return None, templates can check for existence
        # Or, return a default SiteSetting object if that's preferred, though the admin page creates one.
        return {'site_settings': None} # Or SiteSetting() if you want default values always present

    return app

def create_directories(app):
    """필요한 디렉토리 생성"""
    try:
        os.makedirs(app.instance_path, exist_ok=True)

        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(os.path.join(upload_folder, 'thumbnails'), exist_ok=True)

        temp_folder = app.config.get('TEMP_FOLDER')
        if temp_folder:
            os.makedirs(temp_folder, exist_ok=True)

    except OSError as e:
        app.logger.error(f"디렉토리 생성 오류: {e}")

def initialize_extensions(app):
    """Flask 확장 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.public import bp_public
    from app.routes.auth import bp_auth
    from app.routes.admin import bp_admin

    app.register_blueprint(bp_public)
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_admin, url_prefix='/admin')

def register_cli_commands(app):
    """CLI 명령 등록"""
    from app.cli import register_commands
    register_commands(app)

def register_middleware(app):
    """미들웨어 등록"""
    from app.middleware import register_middleware_handlers
    register_middleware_handlers(app)
```

```python
import os
import logging
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from markupsafe import Markup
import datetime
import re

from config import config
from app.database import db
from app.utils.filters import register_template_filters, strip_images_filter, nl2br_filter, mask_ip_filter
from app.utils.logging import setup_logging
from app.utils.context_processors import register_context_processors
from app.utils import file_utils

# 서비스 레이어 임포트
from app.services import (
    PostService,
    UserService,
    CategoryService,
    MediaService
)

# 서비스 레이어 인스턴스 생성
post_service = PostService()
user_service = UserService()
category_service = CategoryService()
media_service = MediaService()

# 유틸리티 인스턴스
file_util = file_utils

# 확장 인스턴스
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""

    # 설정 환경 결정
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # Flask 애플리케이션 생성
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # 로깅 설정
    setup_logging(app)

    # 필요한 디렉토리 생성
    create_directories(app)

    # 확장 초기화
    initialize_extensions(app)

    # 템플릿 필터 등록
    register_template_filters(app)

    # 컨텍스트 프로세서 등록
    register_context_processors(app)

    # 블루프린트 등록
    register_blueprints(app)

    # CLI 명령 등록
    register_cli_commands(app)

    # 미들웨어 등록
    register_middleware(app)

    # 서비스 인스턴스를 애플리케이션 컨텍스트에 등록
    @app.context_processor
    def inject_services():
        return {
            'post_service': post_service,
            'user_service': user_service,
            'category_service': category_service,
            'media_service': media_service
        }
    
    app.logger.info('애플리케이션이 시작되었습니다.')

    # Import PageView model here to avoid circular import if it was at the top
    from app.models import PageView, SiteSetting

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

def create_directories(app):
    """필요한 디렉토리 생성"""
    try:
        os.makedirs(app.instance_path, exist_ok=True)

        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(os.path.join(upload_folder, 'thumbnails'), exist_ok=True)

        temp_folder = app.config.get('TEMP_FOLDER')
        if temp_folder:
            os.makedirs(temp_folder, exist_ok=True)

    except OSError as e:
        app.logger.error(f"디렉토리 생성 오류: {e}")

def initialize_extensions(app):
    """Flask 확장 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.public import bp_public
    from app.routes.auth import bp_auth
    from app.routes.admin import bp_admin

    app.register_blueprint(bp_public)
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_admin, url_prefix='/admin')

def register_cli_commands(app):
    """CLI 명령 등록"""
    from app.cli import register_commands
    register_commands(app)

def register_middleware(app):
    """미들웨어 등록"""
    from app.middleware import register_middleware_handlers
    register_middleware_handlers(app)
```

```python
import os
import logging
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from markupsafe import Markup
import datetime
import re

from config import config
from app.database import db
from app.utils.filters import register_template_filters, strip_images_filter, nl2br_filter, mask_ip_filter
from app.utils.logging import setup_logging
from app.utils.context_processors import register_context_processors
from app.utils import file_utils

# 서비스 레이어 임포트
from app.services import (
    PostService,
    UserService,
    CategoryService,
    MediaService
)

# 서비스 레이어 인스턴스 생성
post_service = PostService()
user_service = UserService()
category_service = CategoryService()
media_service = MediaService()

# 유틸리티 인스턴스
file_util = file_utils

# 확장 인스턴스
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""

    # 설정 환경 결정
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # Flask 애플리케이션 생성
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # 로깅 설정
    setup_logging(app)

    # 필요한 디렉토리 생성
    create_directories(app)

    # 확장 초기화
    initialize_extensions(app)

    # 템플릿 필터 등록
    register_template_filters(app)

    # 컨텍스트 프로세서 등록
    register_context_processors(app)

    # 블루프린트 등록
    register_blueprints(app)

    # CLI 명령 등록
    register_cli_commands(app)

    # 미들웨어 등록
    register_middleware(app)

    # 서비스 인스턴스를 애플리케이션 컨텍스트에 등록
    @app.context_processor
    def inject_services():
        return {
            'post_service': post_service,
            'user_service': user_service,
            'category_service': category_service,
            'media_service': media_service
        }
    
    app.logger.info('애플리케이션이 시작되었습니다.')

    # Import PageView model here to avoid circular import if it was at the top
    from app.models import PageView, SiteSetting

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

def create_directories(app):
    """필요한 디렉토리 생성"""
    try:
        os.makedirs(app.instance_path, exist_ok=True)

        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(os.path.join(upload_folder, 'thumbnails'), exist_ok=True)

        temp_folder = app.config.get('TEMP_FOLDER')
        if temp_folder:
            os.makedirs(temp_folder, exist_ok=True)

    except OSError as e:
        app.logger.error(f"디렉토리 생성 오류: {e}")

def initialize_extensions(app):
    """Flask 확장 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.public import bp_public
    from app.routes.auth import bp_auth
    from app.routes.admin import bp_admin

    app.register_blueprint(bp_public)
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_admin, url_prefix='/admin')

def register_cli_commands(app):
    """CLI 명령 등록"""
    from app.cli import register_commands
    register_commands(app)

def register_middleware(app):
    """미들웨어 등록"""
    from app.middleware import register_middleware_handlers
    register_middleware_handlers(app)

from app.cli import register_commands
from app.middleware import register_middleware_handlers

register_template_filters = register_template_filters
register_context_processors = register_context_processors
setup_logging = setup_logging
strip_images_filter = strip_images_filter
nl2br_filter = nl2br_filter
mask_ip_filter = mask_ip_filter