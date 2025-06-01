"""
Admin post management routes.
Contains routes for creating, editing, and deleting blog posts.
"""

import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound, BadRequest

from app import post_service, category_service, db
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
    
    # 서비스 레이어를 사용하여 포스트 목록 조회
    posts_data = post_service.get_posts(
        page=page,
        per_page=per_page,
        include_unpublished=True  # 관리자용이므로 미공개 포스트도 포함
    )
    
    # 페이지네이션 정보를 딕셔너리로 생성
    pagination = {
        'page': posts_data['page'],
        'per_page': posts_data['per_page'],
        'total': posts_data['total'],
        'pages': posts_data['pages'],
        'items': posts_data['items']
    }
    
    return render_template('admin/admin_posts_list.html', 
                          title='게시물 관리', 
                          posts=posts_data['items'], 
                          pagination=pagination,
                          current_user=current_user)


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
        try:
            # Handle file upload
            cover_image = request.files.get('cover_image')
            cover_image_filename = None
            
            if cover_image and cover_image.filename != '':
                if not allowed_file(cover_image.filename):
                    flash('허용되지 않는 파일 형식입니다. 이미지 파일만 업로드 가능합니다.', 'danger')
                    return render_template('admin/edit_post.html', 
                                         title='새 글 작성', 
                                         form=form, 
                                         current_user=current_user)
                
                try:
                    cover_image_filename = save_cover_image(cover_image)
                except Exception as e:
                    current_app.logger.error(f'Error saving cover image: {e}')
                    flash('커버 이미지 저장 중 오류가 발생했습니다.', 'danger')
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
                'author_id': current_user.id,
                'image_filename': cover_image_filename,  # cover_image -> image_filename
                'category_id': int(form.category.data) if form.category.data and int(form.category.data) > 0 else None,
                'tags': form.tags.data if isinstance(form.tags.data, list) else (form.tags.data.split(',') if form.tags.data else [])
            }
            
            # Handle publishing status
            if 'publish' in request.form and request.form['publish'] == 'true':
                post_data['is_published'] = True
                post_data['published_at'] = datetime.utcnow()
                current_app.logger.info("새 게시물 발행됨")
            
            # 서비스 레이어를 사용하여 포스트 생성
            author_id = post_data.pop('author_id')  # author_id를 추출
            post = post_service.create_post(post_data, author_id=author_id)
            
            flash('글이 성공적으로 작성되었습니다.', 'success')
            return redirect(url_for('admin.admin_posts'))
            
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
            # Handle file upload if a new image is provided
            cover_image = request.files.get('cover_image')
            cover_image_filename = post.image_filename  # cover_image -> image_filename
            
            if cover_image and cover_image.filename != '':
                if not allowed_file(cover_image.filename):
                    flash('허용되지 않는 파일 형식입니다. 이미지 파일만 업로드 가능합니다.', 'danger')
                    return render_template('admin/edit_post.html', 
                                         title='글 수정',
                                         form=form, 
                                         post=post,
                                         current_user=current_user)
                
                try:
                    # Delete old cover image if exists
                    if post.image_filename:  # cover_image -> image_filename
                        delete_cover_image(post.image_filename)  # cover_image -> image_filename
                    
                    # Save new cover image
                    cover_image_filename = save_cover_image(cover_image)
                except Exception as e:
                    current_app.logger.error(f'Error updating cover image: {e}')
                    flash('커버 이미지 업데이트 중 오류가 발생했습니다.', 'danger')
                    return render_template('admin/edit_post.html', 
                                         title='글 수정',
                                         form=form, 
                                         post=post,
                                         current_user=current_user)
            
            # Prepare update data
            update_data = {
                'title': form.title.data,
                'content': form.content.data,
                'excerpt': form.excerpt.data or None,
                'is_published': form.is_published.data,
                'meta_title': form.meta_title.data or None,
                'meta_description': form.meta_description.data or None,
                'category_id': int(form.category.data) if form.category.data and int(form.category.data) > 0 else None,
                'tags': form.tags.data if isinstance(form.tags.data, list) else (form.tags.data.split(',') if form.tags.data else []),
                'image_filename': cover_image_filename  # cover_image -> image_filename
            }
            
            # Handle publishing status
            if 'publish' in request.form and request.form['publish'] == 'true' and not post.is_published:
                update_data['is_published'] = True
                update_data['published_at'] = datetime.utcnow()
                current_app.logger.info("게시물 상태 변경: 발행됨")
            elif 'unpublish' in request.form and request.form['unpublish'] == 'true' and post.is_published:
                update_data['is_published'] = False
                update_data['published_at'] = None
                current_app.logger.info("게시물 상태 변경: 초안으로 변경")
            
            # 서비스 레이어를 사용하여 포스트 업데이트
            updated_post = post_service.update_post(post.id, update_data)
            
            if not updated_post:
                raise Exception("Failed to update post")
            
            flash('글이 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('admin.admin_posts'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating post: {e}')
            flash('글 수정 중 오류가 발생했습니다. 나중에 다시 시도해주세요.', 'danger')
    
    # For GET request, populate form fields
    if request.method == 'GET':
        form.tags.data = post.tags
        if post.category_id:
            form.category.data = post.category_id
    
    # Prepare current image URLs if they exist
    current_image_url = None
    current_thumbnail_url = None
    if post.image_filename:
        current_image_url = url_for('static', filename=f'uploads/{post.image_filename}')
    
    return render_template('admin/edit_post.html',
                         title='글 수정',
                         form=form,
                         post=post,
                         current_user=current_user,
                         current_image_url=current_image_url,
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
