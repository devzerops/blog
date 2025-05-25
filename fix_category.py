from app import create_app, db
from app.models import Post, Category
import sys

app = create_app()

def list_categories():
    """List all categories in the database"""
    categories = Category.query.all()
    print(f"\nTotal categories: {len(categories)}")
    for cat in categories:
        post_count = Post.query.filter_by(category_id=cat.id).count()
        print(f"Category ID: {cat.id}, Name: {cat.name}, Posts: {post_count}")

def check_posts():
    """Check all posts and their assigned categories"""
    posts = Post.query.all()
    print(f"\nTotal posts: {len(posts)}")
    for post in posts:
        category_name = post.category.name if post.category else "No Category"
        print(f"Post ID: {post.id}, Title: {post.title[:30]}, Category ID: {post.category_id}, Category: {category_name}")

def fix_post_category(post_id, category_id):
    """Fix the category for a specific post"""
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
    """Create a test post with specified category"""
    from app.models import User
    
    # Get the first admin user
    user = User.query.first()
    if not user:
        print("Error: No users found in database!")
        return False
    
    # Create a new post
    post = Post(
        title=title,
        content="Test content created by fix_category.py script",
        user_id=user.id,
        is_published=True,
        category_id=category_id
    )
    
    db.session.add(post)
    db.session.commit()
    
    category_name = "None" if category_id is None else Category.query.get(category_id).name
    print(f"Created test post ID {post.id} with title '{title}' and category ID {category_id} ({category_name})")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_category.py list        - List all categories")
        print("  python fix_category.py check       - Check all posts and their categories")
        print("  python fix_category.py fix POST_ID CATEGORY_ID - Fix category for a post")
        print("  python fix_category.py create TITLE CATEGORY_ID - Create test post with category")
        return
    
    command = sys.argv[1]
    
    with app.app_context():
        if command == "list":
            list_categories()
        
        elif command == "check":
            check_posts()
        
        elif command == "fix" and len(sys.argv) >= 4:
            post_id = int(sys.argv[2])
            category_id = None if sys.argv[3].lower() == "none" else int(sys.argv[3])
            fix_post_category(post_id, category_id)
        
        elif command == "create" and len(sys.argv) >= 3:
            title = sys.argv[2]
            category_id = None if len(sys.argv) < 4 or sys.argv[3].lower() == "none" else int(sys.argv[3])
            create_test_post(title, category_id)
        
        else:
            print("Invalid command or missing arguments")

if __name__ == "__main__":
    main()
