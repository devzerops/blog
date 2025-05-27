"""
데이터베이스 테스트 파일. DB 연결 및 스키마 검증을 포함합니다.
"""
import pytest
from sqlalchemy import inspect

from app.database import db
from app.models import User, Post, Category, Comment, SiteSetting

class TestDatabase:
    """데이터베이스 테스트 클래스"""
    
    def test_db_connection(self, app):
        """데이터베이스 연결 테스트"""
        with app.app_context():
            # 간단한 쿼리 실행으로 연결 테스트
            result = db.session.execute('SELECT 1').scalar()
            assert result == 1
    
    def test_tables_exist(self, app):
        """모든 테이블이 존재하는지 테스트"""
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            assert 'user' in tables
            assert 'post' in tables
            assert 'category' in tables
            assert 'comment' in tables
            assert 'site_setting' in tables
    
    def test_relationships(self, app, db):
        """모델 관계 테스트"""
        with app.app_context():
            # 사용자와 게시물 관계
            user = User(username='testuser')
            post = Post(title='Test Post', content='Test Content')
            user.posts.append(post)
            db.session.add_all([user, post])
            db.session.commit()
            
            assert post in user.posts
            assert post.author == user
            
            # 게시물과 댓글 관계
            comment = Comment(nickname='tester', content='Test Comment')
            post.comments.append(comment)
            db.session.add(comment)
            db.session.commit()
            
            assert comment in post.comments
            assert comment.post == post
            
            # 카테고리와 게시물 관계
            category = Category(name='Test Category')
            post.category = category
            db.session.add(category)
            db.session.commit()
            
            assert post.category == category
            assert post in category.posts
