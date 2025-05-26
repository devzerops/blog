"""
데이터베이스 구조 테스트
게시글, 카테고리 등 데이터베이스 구조를 확인합니다.
"""
from app import create_app
from app.models import Post, Category

def check_post_count():
    """게시글 수 확인"""
    app = create_app()
    with app.app_context():
        print('게시글 수:', Post.query.count())
        return Post.query.count()

def check_post_categories():
    """게시글별 카테고리 정보 확인"""
    app = create_app()
    with app.app_context():
        print('\n게시글별 카테고리 정보:')
        for p in Post.query.all():
            print(f'ID: {p.id}, 제목: {p.title}, 카테고리 ID: {p.category_id}')
        return True

def check_categories():
    """카테고리 목록 확인"""
    app = create_app()
    with app.app_context():
        print('\n카테고리 목록:')
        for c in Category.query.all():
            print(f'ID: {c.id}, 이름: {c.name}')
        return Category.query.count()

def run_all_checks():
    """모든 데이터베이스 구조 확인 테스트 실행"""
    check_post_count()
    check_post_categories()
    check_categories()

if __name__ == "__main__":
    run_all_checks()
