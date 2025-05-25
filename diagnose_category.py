from app import create_app, db
from app.models import Post, Category
import sys
from sqlalchemy import inspect

app = create_app()

def print_form_fields(form):
    """Print details about the form fields"""
    print(f"\n=== Form Fields for {form.__class__.__name__} ===")
    for field_name, field in form._fields.items():
        field_type = type(field).__name__
        field_value = field.data
        print(f"Field: {field_name}, Type: {field_type}, Value: {repr(field_value)}")
        if hasattr(field, 'query_factory'):
            print(f"  - Has query_factory: {field.query_factory}")
        if hasattr(field, 'get_pk'):
            print(f"  - Has get_pk function")
        if hasattr(field, 'get_label'):
            print(f"  - get_label function: {field.get_label}")

def test_category_field():
    """Test how the category QuerySelectField works"""
    from app.forms import PostForm
    
    form = PostForm()
    
    # Check the category field details
    category_field = form.category
    print(f"\n=== Category Field Details ===")
    print(f"Field type: {type(category_field).__name__}")
    print(f"Query factory: {category_field.query_factory}")
    print(f"Allow blank: {category_field.allow_blank}")
    print(f"Blank text: {category_field.blank_text}")
    
    # Execute the query factory to get categories
    categories = category_field.query_factory()
    print(f"\n=== Available Categories ===")
    for cat in categories:
        print(f"ID: {cat.id}, Name: {cat.name}")
    
    # Test setting a category value
    if categories:
        category_field.data = categories[0]
        print(f"\n=== After Setting Category ===")
        print(f"Field data: {category_field.data}")
        print(f"Field data type: {type(category_field.data).__name__}")
        
        # Test what happens during form validation/processing
        process_value = category_field.data
        print(f"\n=== During Processing ===")
        print(f"Process value: {process_value}")
        print(f"Process value type: {type(process_value).__name__}")
        print(f"Will be saved as category_id: {process_value.id if process_value else None}")

def fix_problem_posts():
    """Find and fix posts with category issues"""
    print("\n=== Scanning for Posts with Category Issues ===")
    
    # Get all posts
    posts = Post.query.all()
    problem_count = 0
    
    for post in posts:
        # Check if post has category_id but no category
        if post.category_id is not None and post.category is None:
            problem_count += 1
            print(f"Problem post: ID {post.id}, Title: {post.title}, category_id: {post.category_id}")
            
            # Check if the category exists
            category = Category.query.get(post.category_id)
            if category:
                print(f"  - Category exists (ID: {category.id}, Name: {category.name}), but relationship is broken")
            else:
                print(f"  - Category with ID {post.category_id} does not exist")
                # Clear the invalid category_id
                post.category_id = None
                db.session.commit()
                print(f"  - Fixed: Cleared invalid category_id")
    
    if problem_count == 0:
        print("No posts with category issues found")

def check_form_submission():
    """Simulate a form submission with category data"""
    from app.forms import PostForm
    from werkzeug.datastructures import MultiDict
    
    # Create a MultiDict to simulate form data
    form_data = MultiDict([
        ('title', 'Test Post'),
        ('content', 'Test content'),
        ('category', '1'),  # This is usually the ID as a string in the form submission
        ('tags', 'test, category')
    ])
    
    # Create the form with the data
    form = PostForm(form_data)
    
    print("\n=== Simulated Form Submission ===")
    print(f"Raw form data: {form_data}")
    
    # Manually process the category field
    print("\n=== Processing Category Field ===")
    if 'category' in form_data:
        category_id = form_data['category']
        print(f"Category ID from form: {category_id}")
        
        # Try to get the category
        category = Category.query.get(category_id)
        if category:
            print(f"Found category: ID {category.id}, Name: {category.name}")
            
            # Now check what happens when we validate the form
            if form.validate():
                print("Form validated successfully")
                print(f"Category data after validation: {form.category.data}")
                print(f"Type: {type(form.category.data).__name__}")
            else:
                print("Form validation failed")
                for field, errors in form.errors.items():
                    print(f"  - {field}: {errors}")
        else:
            print(f"No category found with ID {category_id}")

def fix_all_categories():
    """Assign a test category to all posts for testing"""
    print("\n=== Assigning Test Category to All Posts ===")
    
    # Get first category
    category = Category.query.first()
    if not category:
        print("No categories found. Creating a test category...")
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.commit()
        print(f"Created test category: ID {category.id}, Name: {category.name}")
    
    # Update all posts
    posts = Post.query.all()
    for post in posts:
        post.category_id = category.id
        print(f"Assigned category to post ID {post.id}: {post.title}")
    
    db.session.commit()
    print(f"Updated {len(posts)} posts with category ID {category.id}")

def main():
    with app.app_context():
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python diagnose_category.py test_field   - Test category field functionality")
            print("  python diagnose_category.py fix_posts    - Find and fix posts with category issues")
            print("  python diagnose_category.py check_form   - Simulate a form submission")
            print("  python diagnose_category.py fix_all      - Assign a test category to all posts")
            return
        
        command = sys.argv[1]
        
        if command == "test_field":
            from app.forms import PostForm
            form = PostForm()
            print_form_fields(form)
            test_category_field()
        
        elif command == "fix_posts":
            fix_problem_posts()
        
        elif command == "check_form":
            check_form_submission()
        
        elif command == "fix_all":
            fix_all_categories()
        
        else:
            print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
