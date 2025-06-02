"""
Admin post management routes.
Contains routes for creating, editing, and deleting blog posts.
"""

import os
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, current_app, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound, BadRequest

from app import post_service, category_service, db
from app.forms import PostForm
from app.auth import admin_required, token_required
from app.routes.admin import bp_admin
from app.utils.image_utils import save_cover_image, delete_cover_image

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp_admin.route('/posts', methods=['GET'])
@admin_required
def admin_posts(current_user):
    """Redirect to admin dashboard"""
    return redirect(url_for('admin.dashboard'))


@bp_admin.route('/post/new', methods=['GET', 'POST'])
@admin_required
def new_post(current_user):
    """Create a new blog post"""
    form = PostForm()
    
    # Load categories for selection
    categories = category_service.get_all_categories()
    form.category.choices = [(0, '-- 카테고리 없음 --')] + [
        (c.id, c.name) for c in categories
    ]
    
    # Process form submission
    if form.validate_on_submit():
        try:
            # 이미지 파일 처리
            thumbnail_filename = None
            
            # 이미지가 있는지 확인하고 저장
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '' and allowed_file(image.filename):
                    try:
                        # 파일 포인터 초기화
                        if hasattr(image, 'seek'):
                            image.seek(0)
                        
                        # 이미지 저장 (썸네일만 사용)
                        _, thumbnail_filename = save_cover_image(image)
                        if not thumbnail_filename:
                            raise ValueError('이미지 처리에 실패했습니다. 다른 이미지로 시도해주세요.')
                            
                        current_app.logger.info(f'썸네일 이미지가 성공적으로 저장되었습니다: {thumbnail_filename}')
                    except Exception as e:
                        current_app.logger.error(f'이미지 저장 중 오류: {str(e)}', exc_info=True)
                        flash(f'이미지 처리 중 오류가 발생했습니다: {str(e)}', 'danger')
                        return render_template('admin/edit_post.html',
                                            title='새 글 작성',
                                            form=form,
                                            current_user=current_user)
            
            # Prepare post data
            post_data = {
                'title': form.title.data,
                'content': form.content.data,
                'excerpt': form.excerpt.data or None,
                'is_published': form.is_published.data,
                'category_id': int(form.category.data) if form.category.data and int(form.category.data) > 0 else None,
                'tags': form.tags.data if isinstance(form.tags.data, list) else (form.tags.data.split(',') if form.tags.data else [])
            }
            
            # 썸네일 파일명이 있는 경우에만 추가
            if thumbnail_filename:
                post_data['thumbnail_filename'] = thumbnail_filename
            
            # Handle publishing status
            if 'publish' in request.form and request.form['publish'] == 'true':
                post_data['is_published'] = True
                post_data['published_at'] = datetime.now(timezone.utc)
                # 게시물 초안 저장
            elif 'save_draft' in request.form and request.form['save_draft'] == 'true':
                post_data['is_published'] = False
            # 서비스 레이어를 사용하여 포스트 생성
            post = post_service.create_post(post_data, current_user.id)
            
            flash('글이 성공적으로 작성되었습니다.', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating post: {e}')
            flash('글 작성 중 오류가 발생했습니다. 나중에 다시 시도해주세요.', 'danger')
    
    return render_template('admin/edit_post.html',
                         title='새 글 작성',
                         form=form,
                         current_user=current_user,
                         current_image_url=None)


@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_post(current_user, post_id):
    """Edit an existing blog post"""
    # 서비스 레이어를 사용하여 포스트 조회
    post = post_service.get_post_by_id(post_id)
    if not post:
        abort(404)
    
    form = PostForm(obj=post)
    
    # 카테고리 목록 로드
    categories = category_service.get_all_categories()
    form.category.choices = [(0, '-- 카테고리 없음 --')] + [
        (c.id, c.name) for c in categories
    ]
    
    if form.validate_on_submit():
        try:
            # Get the post data
            update_data = {
                'title': form.title.data,
                'content': form.content.data,
                'excerpt': form.excerpt.data or None,
                'meta_title': form.meta_title.data or None,
                'meta_description': form.meta_description.data or None,
                'category_id': int(form.category.data) if form.category.data and int(form.category.data) > 0 else None,
                'tags': form.tags.data if isinstance(form.tags.data, list) else (form.tags.data.split(',') if form.tags.data else []),
            }
            
            # Handle publishing status
            if 'save_draft' in request.form:
                update_data['is_published'] = False
            elif 'publish' in request.form:
                update_data['is_published'] = True
                if not post.published_at:  # First time publishing
                    update_data['published_at'] = datetime.now(timezone.utc)
            elif 'unpublish' in request.form:
                update_data['is_published'] = False
            
            # Handle image upload
            image = request.files.get('image')
            if image and hasattr(image, 'filename') and image.filename.strip():
                # Delete old thumbnail if exists
                if post.thumbnail_filename:
                    result = delete_cover_image(post.thumbnail_filename)
                    if not result['success']:
                        current_app.logger.error(f"썸네일 삭제 실패: {result.get('message', '알 수 없는 오류')}")
                
                # Save new thumbnail (only thumbnail is used now)
                try:
                    _, thumbnail_filename = save_cover_image(image)
                    if not thumbnail_filename:
                        raise ValueError('이미지 처리에 실패했습니다. 다른 이미지로 시도해주세요.')
                        
                    update_data['thumbnail_filename'] = thumbnail_filename
                    current_app.logger.info(f'새 썸네일 이미지가 성공적으로 저장되었습니다: {thumbnail_filename}')
                except Exception as e:
                    current_app.logger.error(f'이미지 저장 중 오류: {str(e)}', exc_info=True)
                    flash(f'이미지 처리 중 오류가 발생했습니다: {str(e)}', 'danger')
                    return render_template('admin/edit_post.html',
                                        title='글 수정',
                                        form=form,
                                        post=post,
                                        current_user=current_user)
            # No else needed - if no new image, we don't update the thumbnail
            
            # Update the post
            updated_post = post_service.update_post(post.id, update_data)
            
            if not updated_post:
                raise Exception("Failed to update post")
            
            flash('글이 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating post: {e}')
            flash('글 수정 중 오류가 발생했습니다. 나중에 다시 시도해주세요.', 'danger')

    # For GET request, populate form fields
    if request.method == 'GET':
        form.tags.data = post.tags
        if post.category_id:
            form.category.data = post.category_id
    
    # Prepare current thumbnail URL if it exists
    current_thumbnail_url = None
    if post.thumbnail_filename:
        current_thumbnail_url = url_for('static', filename=f'uploads/thumbnails/{post.thumbnail_filename}')
    
    return render_template('admin/edit_post.html',
                         title='글 수정',
                         form=form,
                         post=post,
                         current_user=current_user,
                         current_thumbnail_url=current_thumbnail_url)


@bp_admin.route('/post/delete/<int:post_id>', methods=['POST'])
@token_required
def delete_post(current_user, post_id):
    """Delete a blog post"""
    try:
        # 서비스 레이어를 사용하여 포스트 삭제
        success = post_service.delete_post(post_id)
        
        if not success:
            raise Exception("Failed to delete post")
        
        flash('글이 성공적으로 삭제되었습니다.', 'success')
        return redirect(url_for('admin.admin_posts'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting post: {e}')
        flash('글 삭제 중 오류가 발생했습니다. 나중에 다시 시도해주세요.', 'danger')
        return redirect(url_for('admin.admin_posts'))
