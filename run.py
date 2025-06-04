import os
from dotenv import load_dotenv
import logging
from app import create_app, db
from app.models import User, Post, Category, Comment, SiteSetting, PageView, Media

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# .env 파일 로드
load_dotenv()

app = create_app()

# Flask 앱 로거 설정
app.logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Post': Post, 
        'Category': Category, 
        'Comment': Comment, 
        'SiteSetting': SiteSetting, 
        'PageView': PageView,
        'Media': Media
    }

# 명령줄에서 초기 설정을 위한 함수 추가
@app.cli.command('init-db')
def init_db_command():
    """데이터베이스 초기화 및 기본 데이터 생성"""
    print("데이터베이스 테이블 생성 중...")
    db.create_all()
    
    # 초기 관리자 계정 생성 확인
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_password:
        print("경고: ADMIN_PASSWORD가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return
        
    if not User.query.filter_by(username=admin_username).first():
        print(f"관리자 계정({admin_username}) 생성 중...")
        admin = User(username=admin_username)
        admin.set_password(admin_password)
        db.session.add(admin)
        
        # 기본 사이트 설정 생성
        if not SiteSetting.query.first():
            print("기본 사이트 설정 생성 중...")
            default_settings = SiteSetting(
                site_title='My Flask Blog',
                site_description='A simple blog built with Flask',
                site_domain='example.com',
                posts_per_page=10,
                admin_email='admin@example.com',
                footer_copyright_text='© 2025 My Flask Blog'
            )
            db.session.add(default_settings)
        
        db.session.commit()
        print("초기 설정 완료!")
    else:
        print("관리자 계정이 이미 존재합니다.")
    
    print("데이터베이스 설정 완료!")

if __name__ == '__main__':
    import os
    # Replit 배포 환경에서는 debug=False로 실행
    debug_mode = os.environ.get('REPLIT_DEPLOYMENT') != '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
