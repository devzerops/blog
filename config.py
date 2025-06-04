
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def get_database_uri():
    """데이터베이스 URI 생성"""
    # Replit DATABASE_URL 우선 사용
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Replit의 connection pooler 사용
        if '.us-east-2' in database_url and '-pooler' not in database_url:
            database_url = database_url.replace('.us-east-2', '-pooler.us-east-2')
        return database_url
    
    # PostgreSQL 연결 정보
    db_user = os.environ.get('POSTGRES_USER', 'postgres')
    db_password = os.environ.get('POSTGRES_PASSWORD', '')
    db_host = os.environ.get('POSTGRES_HOST', 'localhost')
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    db_name = os.environ.get('POSTGRES_DB', 'blog_db')
    
    return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

class Config:
    """기본 설정"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL 연결 풀링 및 재연결 설정
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': 3600,  # 1시간마다 연결 재생성
        'pool_pre_ping': True,  # 연결 상태 확인
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'flask_blog_app'
        }
    }
    
    # 애플리케이션 설정
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'defaultadminpassword'
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    TEMP_FOLDER = os.path.join(basedir, 'app', 'static', 'temp')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico', 'svg', 'webp'}
    
    # 세션 설정
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # 블로그 설정
    POSTS_PER_PAGE = 10
    JWT_EXPIRATION_SECONDS = 3600  # 1시간

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False

class TestConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # 별도 테스트 데이터베이스 사용
    POSTGRES_TEST_DB = os.environ.get('POSTGRES_TEST_DB', 'test_blog_db')
    POSTGRES_TEST_USER = os.environ.get('POSTGRES_TEST_USER', 'postgres')
    POSTGRES_TEST_PASSWORD = os.environ.get('POSTGRES_TEST_PASSWORD', '')
    POSTGRES_TEST_HOST = os.environ.get('POSTGRES_TEST_HOST', 'localhost')
    POSTGRES_TEST_PORT = os.environ.get('POSTGRES_TEST_PORT', '5432')
    
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{POSTGRES_TEST_USER}:'
        f'{POSTGRES_TEST_PASSWORD}@{POSTGRES_TEST_HOST}:'
        f'{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}'
    )

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}
