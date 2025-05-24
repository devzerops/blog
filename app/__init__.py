import os
from flask import Flask
from flask_migrate import Migrate
from markupsafe import Markup
from config import Config
from app.database import db
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
import datetime
import re

migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap5()

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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    bootstrap.init_app(app)

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

    from app.routes_admin import bp_admin
    app.register_blueprint(bp_admin, url_prefix='/admin')

    from app.routes_public import bp_public
    app.register_blueprint(bp_public) 

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.datetime.now(datetime.timezone.utc).year}

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
