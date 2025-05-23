import os
from flask import Flask
from flask_migrate import Migrate
from config import Config
from app.database import db
import datetime

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Ensure the upload folder exists as defined in Config
    # It should be an absolute path or relative to app.root_path
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        # Fallback if not set, though it's set in config.py
        upload_folder = os.path.join(app.root_path, 'static', 'uploads') 
        app.config['UPLOAD_FOLDER'] = upload_folder # Ensure it's set for later use
        
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Error creating upload folder {upload_folder}: {e}")
        pass

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes_auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix='/auth')

    from app.routes_admin import bp_admin
    app.register_blueprint(bp_admin, url_prefix='/admin')

    from app.routes_public import bp_public
    app.register_blueprint(bp_public) # No prefix for public, e.g. /posts, /

    # Context processor to inject variables into all templates
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.datetime.now(datetime.timezone.utc).year}

    # CLI command to create admin user
    @app.cli.command('create-admin')
    def create_admin_command():
        """Creates the admin user."""
        from app.models import User
        # from werkzeug.security import generate_password_hash # Not needed here, model handles it
        
        if User.query.filter_by(username='admin').first():
            print('Admin user already exists.')
            return
        
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            default_pw = 'adminpass' # Keep it simple for local dev, emphasize changing it
            print(f'ADMIN_PASSWORD environment variable not set. Using default: {default_pw}')
            admin_password = default_pw
            
        admin = User(username='admin')
        admin.set_password(admin_password) # Uses the method from User model
        db.session.add(admin) # 'db' now refers to the correctly initialized shared instance
        db.session.commit()
        print(f'Admin user created. Please ensure a strong password is used in production (set via ADMIN_PASSWORD env var).')

    return app
