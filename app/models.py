from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db # Use the db instance from database.py

# Association table for the many-to-many relationship between Post and Tag
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

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

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Markdown content
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    
    image_filename = db.Column(db.String(255), nullable=True)
    alt_text = db.Column(db.String(255), nullable=True) # New field for alt text
    video_embed_url = db.Column(db.String(500), nullable=True) # New field for video embed URL

    # New fields for publish status
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)

    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                           backref=db.backref('posts', lazy=True))
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    views = db.Column(db.Integer, default=0, nullable=False)

    # Relationship to comments
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False) # Nickname for anonymous users
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Optional: if you want to link to registered users later
    # author = db.relationship('User', backref=db.backref('comments', lazy='dynamic')) # Optional

    def __repr__(self):
        return f'<Comment {self.id} by {self.nickname}>'
