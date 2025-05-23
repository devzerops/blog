from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db # Use the db instance from database.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Markdown content
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    
    image_filename = db.Column(db.String(128), nullable=True)
    alt_text = db.Column(db.String(255), nullable=True) # New field for alt text
    video_embed_url = db.Column(db.String(256), nullable=True)
    tags = db.Column(db.String(200), nullable=True) # Comma-separated tags
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    views = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'
