"""
Admin post management routes.
Contains routes for creating, editing, and deleting blog posts.
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.exceptions import NotFound
from sqlalchemy import func

from app.database import db
from app.models import Post, Category
from app.forms import PostForm
from app.auth import admin_required, token_required
from app.routes.admin import bp_admin


@bp_admin.route('/posts', methods=['GET'])
@admin_required
def admin_posts(current_user):
    """List all blog posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = posts_pagination.items
    
    return render_template('admin/admin_posts_list.html', 
                          title='게시물 관리', 
                          posts=posts, 
                          pagination=posts_pagination, 
                          current_user=current_user)


@bp_admin.route('/post/new', methods=['GET', 'POST'])
@admin_required
def new_post(current_user):
    """Create a new blog post"""
    form = PostForm()
    
    # Load categories for selection
    form.category.choices = [(0, '-- 카테고리 없음 --')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    
    # Process form submission
    if request.method == 'POST':
        # 폼 유효성 검증 실패 시 오류 로깅
        if not form.validate_on_submit():
            for field, errors in form.errors.items():
                current_app.logger.error(f"Field {field} failed validation with errors: {errors}")
            return render_template('admin/edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)
    
    # 폼 검증 성공
    if form.validate_on_submit():
        # Handle category selection - convert "0" to None
        try:
            category_id = int(request.form.get('category', 0))
            if category_id == 0:
                category_id = None
                current_app.logger.info(f"카테고리 선택 없음, category_id: {category_id}")
            else:
                current_app.logger.info(f"선택된 카테고리 ID: {category_id}")
        except ValueError:
            category_id = None
            current_app.logger.error(f"카테고리 ID 변환 오류: {request.form.get('category')}")
        
        current_app.logger.info(f"최종 사용될 category_id: {category_id}")
        
        # Determine published status from form
        is_published = False
        published_at = None
        
        # Check if publish button was clicked
        if 'publish' in request.form and request.form['publish'] == 'true':
            is_published = True
            published_at = datetime.utcnow()
            current_app.logger.info("게시물 상태: 발행됨")
        else:
            current_app.logger.info("게시물 상태: 초안")
        
        # Create post
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user,
            is_published=is_published,
            published_at=published_at,
            category_id=category_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Assign tags directly as a comma-separated string
        post.tags = form.tags.data
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)


@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_post(current_user, post_id):
    """Edit an existing blog post"""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    
    # Load categories for selection
    form.category.choices = [(0, '-- 카테고리 없음 --')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    
    if request.method == 'POST':
        current_app.logger.info(f"[edit_post] 원시 폼 데이터: {request.form}")
    
    if form.validate_on_submit():
        # Update post data
        post.title = form.title.data
        post.content = form.content.data
        
        # Handle category selection - convert "0" to None
        try:
            category_id = int(request.form.get('category', 0))
            if category_id == 0:
                category_id = None
                current_app.logger.info(f"[edit_post] 카테고리 선택 없음, category_id: {category_id}")
            else:
                current_app.logger.info(f"[edit_post] 선택된 카테고리 ID: {category_id}")
        except ValueError:
            category_id = None
            current_app.logger.error(f"[edit_post] 카테고리 ID 변환 오류: {request.form.get('category')}")
        
        current_app.logger.info(f"[edit_post] 최종 사용될 category_id: {category_id}")
        post.category_id = category_id
        
        # Handle publishing status
        if 'publish' in request.form and request.form['publish'] == 'true' and not post.is_published:
            post.is_published = True
            post.published_at = datetime.utcnow()
            current_app.logger.info("게시물 상태 변경: 발행됨")
        elif 'unpublish' in request.form and request.form['unpublish'] == 'true' and post.is_published:
            post.is_published = False
            post.published_at = None
            current_app.logger.info("게시물 상태 변경: 초안으로 변경")
        
        # Assign tags directly as a comma-separated string
        post.tags = form.tags.data
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # For GET request, populate form fields
    if request.method == 'GET':
        # Populate tags for GET request (already handled by obj=post for other fields)
        form.tags.data = post.tags

    return render_template('admin/edit_post.html', title='Edit Post', form=form, post=post, legend=f'Edit "{post.title}"', current_user=current_user)


@bp_admin.route('/post/delete/<int:post_id>', methods=['POST'])
@token_required
def delete_post(current_user, post_id):
    """Delete a blog post"""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))
