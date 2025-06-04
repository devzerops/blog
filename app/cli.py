
import os
from app.database import db
from app.models import User, SiteSetting

def register_commands(app):
    """CLI 명령 등록"""
    
    @app.cli.command('create-admin')
    def create_admin_command():
        """관리자 계정 생성"""
        if User.query.filter_by(username='admin').first():
            print('관리자 계정이 이미 존재합니다.')
            return
        
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            default_pw = 'adminpass'
            print(f'ADMIN_PASSWORD 환경변수가 설정되지 않았습니다. 기본값 사용: {default_pw}')
            admin_password = default_pw
        
        admin = User(username='admin')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print('관리자 계정이 생성되었습니다.')
    
    @app.cli.command('init-db')
    def init_db_command():
        """데이터베이스 초기화"""
        print("데이터베이스 테이블 생성 중...")
        db.create_all()
        
        # 기본 관리자 계정 생성
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if not admin_password:
            print("경고: ADMIN_PASSWORD가 설정되지 않았습니다.")
            return
        
        if not User.query.filter_by(username=admin_username).first():
            print(f"관리자 계정({admin_username}) 생성 중...")
            admin = User(username=admin_username)
            admin.set_password(admin_password)
            db.session.add(admin)
            
            # 기본 사이트 설정
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
