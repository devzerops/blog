from app import create_app, db
from app.models import Post, Category

app = create_app()

with app.app_context():
    print("\n===== CHECKING POSTS AND CATEGORIES =====")
    
    # Check all categories
    categories = Category.query.all()
    print(f"\nTotal categories: {len(categories)}")
    for cat in categories:
        print(f"Category ID: {cat.id}, Name: {cat.name}")
        
    # Check all posts and their assigned categories
    posts = Post.query.all()
    print(f"\nTotal posts: {len(posts)}")
    for post in posts:
        category_name = post.category.name if post.category else "No Category"
        print(f"Post ID: {post.id}, Title: {post.title[:30]}, Category ID: {post.category_id}, Category: {category_name}")
    
    print("\n===== CHECKING FOR ISSUES =====")
    # Check for posts with category_id but no associated category
    problem_posts = Post.query.filter(Post.category_id.isnot(None)).all()
    for post in problem_posts:
        if not post.category:
            print(f"ERROR: Post ID {post.id} has category_id {post.category_id} but no associated category object!")
    
    print("\n===== DIAGNOSIS COMPLETE =====")
