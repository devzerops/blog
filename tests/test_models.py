"""
모델 테스트 파일. 모든 데이터 모델에 대한 테스트를 포함합니다.
"""
import pytest
from datetime import datetime, timezone

from app.models import User, Post, Category, Comment, SiteSetting

class TestUserModel:
    """User 모델 테스트 클래스"""
    
    def test_password_hashing(self, db):
        """비밀번호 해싱 기능 테스트"""
        user = User(username='testuser')
        user.set_password('testpass123')
        
        assert user.password_hash is not None
        assert user.password_hash != 'testpass123'
        assert user.check_password('testpass123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_repr(self, db):
        """__repr__ 메서드 테스트"""
        user = User(username='testuser')
        db.session.add(user)
        db.session.commit()
        
        assert repr(user) == f'<User {user.username}>'

class TestPostModel:
    """Post 모델 테스트 클래스"""
    
    def test_post_creation(self, db, admin_user):
        """게시물 생성 테스트"""
        post = Post(
            title='Test Post',
            content='Test Content',
            author=admin_user
        )
        db.session.add(post)
        db.session.commit()
        
        assert post.id is not None
        assert post.created_at is not None
        assert post.updated_at is not None
        assert post.author == admin_user
    
    def test_post_image_url(self, db, admin_user):
        """이미지 URL 생성 테스트"""
        post = Post(
            title='Test Post',
            content='Test Content',
            author=admin_user,
            image_filename='test.jpg'
        )
        
        assert post.image_url == '/static/uploads/test.jpg'
        assert post.thumbnail_url is None
        
        post.thumbnail_filename = 'thumb_test.jpg'
        assert post.thumbnail_url == '/static/uploads/thumbnails/thumb_test.jpg'

class TestCategoryModel:
    """Category 모델 테스트 클래스"""
    
    def test_category_creation(self, db):
        """카테고리 생성 테스트"""
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        
        assert category.id is not None
        assert category.name == 'Test Category'
    
    def test_category_post_relationship(self, db, admin_user):
        """카테고리-게시물 관계 테스트"""
        category = Category(name='Test Category')
        post = Post(
            title='Test Post',
            content='Test Content',
            author=admin_user
        )
        post.category = category
        
        db.session.add_all([category, post])
        db.session.commit()
        
        assert post.category == category
        assert post in category.posts

class TestSiteSettingModel:
    """SiteSetting 모델 테스트 클래스"""
    
    def test_default_values(self, db):
        """기본값 테스트"""
        settings = SiteSetting()
        db.session.add(settings)
        db.session.commit()
        
        assert settings.site_title == "My Blog"
        assert settings.posts_per_page == 10
