from app import create_app
from app.models import Post, Category

app = create_app()
with app.app_context():
    print('게시글 수:', Post.query.count())
    print('\n게시글별 카테고리 정보:')
    for p in Post.query.all():
        print(f'ID: {p.id}, 제목: {p.title}, 카테고리 ID: {p.category_id}')
    
    print('\n카테고리 목록:')
    for c in Category.query.all():
        print(f'ID: {c.id}, 이름: {c.name}')
