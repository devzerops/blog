from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db # Use the db instance from database.py
from sqlalchemy import asc
from sqlalchemy.orm import validates

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

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    thumbnail_filename = db.Column(db.String(255), nullable=True)
    alt_text = db.Column(db.String(200), nullable=True)
    video_embed_url = db.Column(db.String(300), nullable=True)
    meta_description = db.Column(db.String(300), nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True, index=True)
    views = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.Column(db.String(255), nullable=True)
    page_views = db.relationship('PageView', backref='post', lazy='dynamic')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    @property
    def image_url(self):
        # 이전 버전과의 호환성을 위해 thumbnail_url을 반환
        return self.thumbnail_url

    @property
    def thumbnail_url(self):
        if self.thumbnail_filename:
            return f'/static/uploads/thumbnails/{self.thumbnail_filename}'
        return None

    def __repr__(self):
        return f'<Post {self.title[:50]}...>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False) # Nickname for anonymous users
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Store full IP (IPv4 or IPv6)

    # For nested comments
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship(
        'Comment', 
        backref=db.backref('parent_comment', remote_side='Comment.id'), 
        lazy='dynamic',
        cascade='all, delete-orphan', # If a parent comment is deleted, its replies are also deleted
        order_by='Comment.created_at' # Use string form for self-referential order_by
    )

    def __repr__(self):
        return f'<Comment {self.id} by {self.nickname}>'

class PageView(db.Model):
    __tablename__ = 'page_view'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # For IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)

    def __repr__(self):
        return f'<PageView {self.path} at {self.timestamp}>'

class Media(db.Model):
    """미디어 파일을 저장하는 모델"""
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    alt_text = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Media {self.original_filename}>'


class SiteSetting(db.Model):
    __tablename__ = 'site_setting' # Explicitly naming the table
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default="My Blog")
    site_description = db.Column(db.Text, nullable=True)
    site_domain = db.Column(db.String(255), nullable=True)
    favicon_filename = db.Column(db.String(255), nullable=True)
    posts_per_page = db.Column(db.Integer, default=10)
    admin_email = db.Column(db.String(120), nullable=True)
    admin_github_url = db.Column(db.String(255), nullable=True)
    ad_sense_code = db.Column(db.Text, nullable=True)
    google_analytics_id = db.Column(db.String(50), nullable=True)
    footer_copyright_text = db.Column(db.String(255), nullable=True, default=" {year} {site_title}. All rights reserved.")
    about_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SiteSetting {self.site_title}>'
