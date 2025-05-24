import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'blog.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'defaultadminpassword'
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
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
