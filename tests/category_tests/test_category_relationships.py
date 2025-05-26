"""
카테고리 관계 테스트
게시글과 카테고리 간의 관계 검증 및 문제 진단
"""
from app import create_app, db
from app.models import Post, Category
import sys

def check_category_post_relationships():
    """게시글과 카테고리 관계 확인"""
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
        
        return True

def check_for_relationship_issues():
    """카테고리 관계 문제 진단"""
    app = create_app()
    with app.app_context():
        print("\n===== CHECKING FOR ISSUES =====")
        # Check for posts with category_id but no associated category
        problem_posts = Post.query.filter(Post.category_id.isnot(None)).all()
        issues_found = False
        
        for post in problem_posts:
            if not post.category:
                print(f"ERROR: Post ID {post.id} has category_id {post.category_id} but no associated category object!")
                issues_found = True
        
        if not issues_found:
            print("No relationship issues found!")
        
        print("\n===== DIAGNOSIS COMPLETE =====")
        return not issues_found

def run_all_tests():
    """모든 카테고리 관계 테스트 실행"""
    check_category_post_relationships()
    check_for_relationship_issues()

if __name__ == "__main__":
    run_all_tests()
