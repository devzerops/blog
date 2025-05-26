"""
Admin dashboard routes.
Contains routes for the admin dashboard and related functionality.
"""

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, current_app
from sqlalchemy import func, desc, and_

from app.database import db
from app.models import Post, Category, Comment, PageView
from app.auth import admin_required, token_required
from app.routes.admin import bp_admin


@bp_admin.route('/')
@bp_admin.route('/dashboard')
@admin_required
def dashboard(current_user):
    """Main admin dashboard route"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = posts_pagination.items
    
    # Format date for display
    for post in posts:
        if post.created_at:
            post.formatted_date = post.created_at.strftime('%Y-%m-%d %H:%M')
        else:
            post.formatted_date = 'N/A'
    
    # Get all categories for filter dropdown
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('admin/admin_dashboard.html', 
        title='관리자 대시보드', 
        posts=posts, 
        pagination=posts_pagination, 
        current_user=current_user,
        categories=categories
    )
