"""
카테고리 수정 및 문제해결 테스트
문제가 있는 카테고리-게시글 관계를 수정하는 유틸리티
"""
from app import create_app, db
from app.models import Post, Category
import sys

def list_categories():
    """데이터베이스의 모든 카테고리 나열"""
    app = create_app()
    with app.app_context():
        categories = Category.query.all()
        print(f"\nTotal categories: {len(categories)}")
        for cat in categories:
            post_count = Post.query.filter_by(category_id=cat.id).count()
            print(f"Category ID: {cat.id}, Name: {cat.name}, Posts: {post_count}")
        return len(categories)

def check_posts():
    """모든 게시글과 할당된 카테고리 확인"""
    app = create_app()
    with app.app_context():
        posts = Post.query.all()
        print(f"\nTotal posts: {len(posts)}")
        for post in posts:
            category_name = post.category.name if post.category else "No Category"
            print(f"Post ID: {post.id}, Title: {post.title[:30]}, Category ID: {post.category_id}, Category: {category_name}")
        return len(posts)

def fix_post_category(post_id, category_id):
    """특정 게시글의 카테고리 수정"""
    app = create_app()
    with app.app_context():
        post = Post.query.get(post_id)
        if not post:
            print(f"Error: Post ID {post_id} not found!")
            return False
        
        if category_id is None:
            post.category_id = None
            db.session.commit()
            print(f"Removed category from post ID {post_id} ({post.title[:30]})")
            return True
        
        category = Category.query.get(category_id)
        if not category:
            print(f"Error: Category ID {category_id} not found!")
            return False
        
        post.category_id = category.id
        db.session.commit()
        print(f"Updated post ID {post_id} ({post.title[:30]}) with category ID {category_id} ({category.name})")
        return True

def create_test_post(title, category_id=None):
    """지정된 카테고리로 테스트 게시글 생성"""
    app = create_app()
    with app.app_context():
        from app.models import User
        
        # Get the first admin user
        user = User.query.first()
        if not user:
            print("Error: No users found in database!")
            return False
        
        # Create a new post
        post = Post(
            title=title,
            content="Test content created by test_category_fix.py script",
            user_id=user.id,
            is_published=True,
            category_id=category_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        category_name = "None" if category_id is None else Category.query.get(category_id).name
        print(f"Created test post ID {post.id} with title '{title}' and category ID {category_id} ({category_name})")
        return True

def run_test(command, *args):
    """테스트 명령 실행"""
    if command == "list":
        return list_categories()
    
    elif command == "check":
        return check_posts()
    
    elif command == "fix" and len(args) >= 2:
        post_id = int(args[0])
        category_id = None if args[1].lower() == "none" else int(args[1])
        return fix_post_category(post_id, category_id)
    
    elif command == "create" and len(args) >= 1:
        title = args[0]
        category_id = None if len(args) < 2 or args[1].lower() == "none" else int(args[1])
        return create_test_post(title, category_id)
    
    else:
        print("Invalid command or missing arguments")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_category_fix.py list        - List all categories")
        print("  python test_category_fix.py check       - Check all posts and their categories")
        print("  python test_category_fix.py fix POST_ID CATEGORY_ID - Fix category for a post")
        print("  python test_category_fix.py create TITLE CATEGORY_ID - Create test post with category")
        sys.exit(1)
    
    command = sys.argv[1]
    run_test(command, *sys.argv[2:])
