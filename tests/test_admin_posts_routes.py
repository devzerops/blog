"""
관리자 게시물 라우트 테스트 파일.
"""
import pytest
import os
from io import BytesIO

from flask import url_for

class TestAdminPostsRoutes:
    """관리자 게시물 라우트 테스트 클래스"""
    
    def test_admin_posts_list(self, client, admin_user):
        """게시물 목록 페이지 테스트"""
        # 로그인
        client.post('/admin/login', data={
            'username': admin_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/admin/posts')
        
        assert response.status_code == 200
        assert b'게시물 관리' in response.data
    
    def test_new_post_creation(self, client, admin_user):
        """새 게시물 생성 테스트"""
        # 로그인
        client.post('/admin/login', data={
            'username': admin_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # 테스트 이미지 생성
        data = {
            'title': 'Test Post',
            'content': 'Test Content',
            'category': '0',
            'tags': 'test,tag',
            'alt_text': 'Test Alt Text'
        }
        
        # 이미지 파일 첨부
        data['image'] = (BytesIO(b'fake image data'), 'test.jpg')
        
        response = client.post(
            '/admin/post/new',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Test Post' in response.data
    
    def test_post_deletion(self, client, admin_user, db):
        """게시물 삭제 테스트"""
        from app.models import Post
        
        # 테스트 게시물 생성
        post = Post(
            title='Test Post',
            content='Test Content',
            author=admin_user
        )
        db.session.add(post)
        db.session.commit()
        
        # 로그인
        client.post('/admin/login', data={
            'username': admin_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.post(
            f'/admin/post/delete/{post.id}',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'게시물이 성공적으로 삭제되었습니다' in response.data
        assert Post.query.get(post.id) is None
