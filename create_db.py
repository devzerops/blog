"""
데이터베이스 직접 생성 스크립트
"""
from app import create_app, db
from app.models import User, Post, Category, Comment, SiteSetting, PageView

app = create_app()

# 애플리케이션 컨텍스트 내에서 실행
with app.app_context():
    print("데이터베이스 생성 중...")
    db.create_all()
    
    # 초기 관리자 계정 생성 확인
    if not User.query.filter_by(username='admin').first():
        print("관리자 계정 생성 중...")
        admin = User(username='admin')
        admin.set_password('adminpass')  # 실제 환경에서는 강력한 비밀번호 사용 필요
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
                footer_text='© 2025 My Flask Blog'
            )
            db.session.add(default_settings)
        
        db.session.commit()
        print("초기 설정 완료!")
    else:
        print("관리자 계정이 이미 존재합니다.")
    
    print("데이터베이스 설정 완료!")
