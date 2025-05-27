"""
테스트 설정 파일. pytest 픽스처와 공통 테스트 설정을 포함합니다.
"""
import pytest
from app import create_app
from app.database import db as _db

@pytest.fixture(scope='session')
def app():
    """Flask 애플리케이션 픽스처"""
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    """데이터베이스 픽스처"""
    _db.create_all()
    yield _db
    _db.drop_all()

@pytest.fixture(scope='function')
def client(app, db):
    """테스트 클라이언트 픽스처"""
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def admin_user(db):
    """관리자 사용자 픽스처"""
    from app.models import User
    user = User(username='admin', password='testpass123')
    user.set_password('testpass123')
    db.session.add(user)
    db.session.commit()
    return user
