"""
Admin post management routes.
Contains routes for creating, editing, and deleting blog posts.
"""

import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from sqlalchemy import func

from app.database import db
from app.models import Post, Category
from app.forms import PostForm
from app.auth import admin_required, token_required
from app.routes.admin import bp_admin
from app.utils.image_utils import save_cover_image, delete_cover_image


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
        current_app.logger.info(f"[new_post] Raw form data: {request.form}")
        current_app.logger.info(f"[new_post] Form data: title={form.title.data}, content length={len(form.content.data) if form.content.data else 0}")
        
        # 수동으로 content 필드 검증
        if not form.content.data or not form.content.data.strip():
            current_app.logger.error("[new_post] Content is empty")
            form.content.errors.append('내용을 입력해주세요.')
            return render_template('admin/edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)
        
        # 폼 유효성 검증 실패 시 오류 로깅
        if not form.validate_on_submit():
            for field, errors in form.errors.items():
                current_app.logger.error(f"[new_post] Field {field} failed validation with errors: {errors}")
            return render_template('admin/edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)
    
    # 폼 검증 성공
    if form.validate_on_submit():
        # Handle category selection - form.category.data는 이미 coerce=int로 처리됨
        category_id = form.category.data if form.category.data != 0 else None
        current_app.logger.info(f"카테고리 ID: {category_id}")
        
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
        
        # Handle file upload and generate thumbnail
        image_filename = None
        thumbnail_filename = None
        if form.image.data:
            try:
                image_filename, thumbnail_filename = save_cover_image(
                    form.image.data,
                    output_size=(1200, 630),  # Standard blog post image size
                    thumbnail_size=(300, 200)  # Thumbnail size
                )
            except Exception as e:
                current_app.logger.error(f"Error processing cover image: {e}")
                flash('이미지 처리 중 오류가 발생했습니다. 다른 이미지로 시도해주세요.', 'error')
                return render_template('admin/edit_post.html', title='New Post', 
                                     form=form, legend='New Post', 
                                     current_user=current_user)

        # Create post
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user,
            is_published=is_published,
            published_at=published_at,
            category_id=category_id,
            image_filename=image_filename,
            thumbnail_filename=thumbnail_filename,
            alt_text=form.alt_text.data
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Assign tags directly as a comma-separated string
        post.tags = form.tags.data
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_post.html', 
                         title='New Post', 
                         form=form, 
                         legend='New Post', 
                         current_user=current_user,
                         current_image_url=None)


@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_post(current_user, post_id):
    """Edit an existing blog post"""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    
    if request.method == 'POST':
        current_app.logger.info(f"[edit_post] 원시 폼 데이터: {request.form}")
    
    if form.validate_on_submit():
        # Handle file upload if a new image is provided
        if form.image.data:
            # Delete old images if they exist
            if post.image_filename or post.thumbnail_filename:
                try:
                    delete_cover_image(post.image_filename, post.thumbnail_filename)
                except Exception as e:
                    current_app.logger.error(f"Error deleting old images: {e}")
            
            # Save the new image and generate thumbnail
            try:
                image_filename, thumbnail_filename = save_cover_image(
                    form.image.data,
                    output_size=(1200, 630),  # Standard blog post image size
                    thumbnail_size=(300, 200)  # Thumbnail size
                )
                post.image_filename = image_filename
                post.thumbnail_filename = thumbnail_filename
            except Exception as e:
                current_app.logger.error(f"Error processing cover image: {e}")
                flash('이미지 처리 중 오류가 발생했습니다. 다른 이미지로 시도해주세요.', 'error')
                return render_template('admin/edit_post.html', 
                                     title='Edit Post', 
                                     form=form, 
                                     post=post, 
                                     legend=f'Edit "{post.title}"', 
                                     current_user=current_user,
                                     current_image_url=url_for('static', filename=f'uploads/{post.image_filename}') if post.image_filename else None)
        
        # Update post data
        post.title = form.title.data
        post.content = form.content.data
        post.alt_text = form.alt_text.data
        
        # Handle category selection - form.category.data는 이미 coerce=int로 처리됨
        category_id = form.category.data if form.category.data != 0 else None
        post.category_id = category_id
        current_app.logger.info(f"[edit_post] 카테고리 ID: {post.category_id}")
        
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

    # Prepare current image URLs if they exist
    current_image_url = None
    current_thumbnail_url = None
    if post.image_filename:
        current_image_url = url_for('static', filename=f'uploads/{post.image_filename}')
        current_thumbnail_url = url_for('static', filename=f'uploads/thumbnails/{post.thumbnail_filename}') if post.thumbnail_filename else None

    return render_template('admin/edit_post.html', 
                         title='Edit Post', 
                         form=form, 
                         post=post, 
                         legend=f'Edit "{post.title}"', 
                         current_user=current_user,
                         current_image_url=current_image_url,
                         current_thumbnail_url=current_thumbnail_url)


@bp_admin.route('/post/delete/<int:post_id>', methods=['POST'])
@token_required
def delete_post(current_user, post_id):
    # Delete a blog post and its associated images
    post = Post.query.get_or_404(post_id)
    
    # Delete associated images if they exist
    if post.image_filename or post.thumbnail_filename:
        try:
            delete_cover_image(post.image_filename, post.thumbnail_filename)
        except Exception as e:
            current_app.logger.error(f"Error deleting image files for post {post_id}: {e}")
    
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    
    flash('게시물이 성공적으로 삭제되었습니다!', 'success')
    return redirect(url_for('admin.dashboard'))
