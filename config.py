import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def get_database_uri():
    db_type = os.environ.get('DB_TYPE', 'sqlite').lower()
    
    if db_type == 'postgresql':
        # PostgreSQL 연결 정보
        db_user = os.environ.get('POSTGRES_USER', 'postgres')
        db_password = os.environ.get('POSTGRES_PASSWORD', '')
        db_host = os.environ.get('POSTGRES_HOST', 'localhost')
        db_port = os.environ.get('POSTGRES_PORT', '5432')
        db_name = os.environ.get('POSTGRES_DB', 'blog_db')
        return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    else:
        # SQLite (기본값)
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'blog.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f'sqlite:///{db_path}'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'defaultadminpassword'
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    TEMP_FOLDER = os.path.join(basedir, 'app', 'static', 'temp')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico', 'svg', 'webp'}
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # Bootstrap-Flask basic config (example)
    BOOTSTRAP_BTN_STYLE = 'btn-primary' 

    # Custom configurations for the blog
    POSTS_PER_PAGE = 10
    JWT_EXPIRATION_SECONDS = 3600 # 1 hour

class DevelopmentConfig(Config):
    # TINYMCE_API_KEY = os.environ.get('TINYMCE_API_KEY') # Removed for self-hosted
    pass


class TestConfig(Config):
    """Configuration for testing with a separate test database"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Use a separate test database
    POSTGRES_TEST_DB = os.environ.get('POSTGRES_DB', 'test_blog_db')
    POSTGRES_TEST_USER = os.environ.get('POSTGRES_TEST_USER', 'postgres')
    POSTGRES_TEST_PASSWORD = os.environ.get('POSTGRES_TEST_PASSWORD', '')
    POSTGRES_TEST_HOST = os.environ.get('POSTGRES_TEST_HOST', 'localhost')
    POSTGRES_TEST_PORT = os.environ.get('POSTGRES_TEST_PORT', '5432')
    
    # Override the database URI for testing
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{POSTGRES_TEST_USER}:'
        f'{POSTGRES_TEST_PASSWORD}@{POSTGRES_TEST_HOST}:'
        f'{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}'
    )
    
    # Speed up tests by using a faster password hashing algorithm
    PASSWORD_HASH = 'plaintext'  # Only for testing, never use in production!
