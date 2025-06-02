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

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            current_app.logger.info(f'Form data: {request.form}')
            current_app.logger.info(f'Files received: {request.files}')
            # 이미지 파일 처리
            current_app.logger.info('Checking for uploaded files...')
            image = request.files.get('image')
            cover_image_filename = None
            thumbnail_filename = None
            
            # 요청의 모든 파일 정보 로깅
            current_app.logger.info(f'Request files: {request.files}')
            current_app.logger.info(f'Request form data: {request.form}')
            current_app.logger.info(f'Request headers: {dict(request.headers)}')
            
            if image and hasattr(image, 'filename') and image.filename:
                current_app.logger.info(f'Processing image: {image.filename}')
                current_app.logger.info(f'Image object: {image}')
                current_app.logger.info(
                    f'Image filename: {image.filename}, '
                    f'Content-Type: {image.content_type}, '
                    f'Content-Length: {image.content_length if hasattr(image, "content_length") else "N/A"}'
                )
                
                # 파일 포인터를 처음으로 되돌림
                if hasattr(image, 'seek'):
                    image.seek(0, 2)  # 파일 끝으로 이동
                    file_size = image.tell()
                    image.seek(0)  # 다시 파일 시작으로 되돌림
                    current_app.logger.info(f'Actual file size from stream: {file_size} bytes')
                    
                    if file_size == 0:
                        error_msg = '업로드된 파일이 비어 있습니다.'
                        current_app.logger.warning(error_msg)
                        flash(error_msg, 'danger')
                        return render_template('admin/new_post.html', title='New Post', form=form)
                
                # 파일이 비어있는지 확인
                if not image.filename.strip():
                    current_app.logger.warning('No filename provided or filename is empty')
                    flash('파일을 선택해주세요.', 'warning')
                
                # 파일 크기 확인 (최대 10MB)
                max_size = 10 * 1024 * 1024  # 10MB
                if hasattr(image, 'content_length') and image.content_length > max_size:
                    error_msg = '파일 크기가 너무 큽니다. 10MB 이하의 파일만 업로드 가능합니다.'
                    current_app.logger.warning(error_msg)
                    flash(error_msg, 'danger')
                    return render_template('admin/new_post.html', title='New Post', form=form)
                
                # 파일 확장자 확인
                if '.' not in image.filename:
                    current_app.logger.warning(f'Invalid filename (no extension): {image.filename}')
                    flash('유효하지 않은 파일 이름입니다. 확장자가 포함되어야 합니다.', 'warning')
                    return render_template('admin/new_post.html', title='New Post', form=form)
                
                if not allowed_file(image.filename):
                    error_msg = f'허용되지 않는 파일 형식입니다: {image.filename}. 허용되는 형식: {ALLOWED_EXTENSIONS}'
                    current_app.logger.warning(error_msg)
                    flash(error_msg, 'danger')
                    return render_template('admin/new_post.html', title='New Post', form=form)
                
                try:
                    # 파일 저장 시도
                    current_app.logger.info('Attempting to save image...')
                    cover_image_filename, thumbnail_filename = save_cover_image(image)
                    current_app.logger.info(f'Image saved successfully: {cover_image_filename}, Thumbnail: {thumbnail_filename}')
                except Exception as e:
                    current_app.logger.error(f'Error saving image: {str(e)}', exc_info=True)
                    flash(f'이미지 저장 중 오류가 발생했습니다: {str(e)}', 'danger')
                    return render_template('admin/new_post.html', title='New Post', form=form)
            else:
                current_app.logger.info('No image file was uploaded or image is empty')
                cover_image_filename = None
                thumbnail_filename = None
            
            # Prepare post data
            post_data = {
                'title': form.title.data,
                'content': form.content.data,
                'excerpt': form.excerpt.data or None,
                'is_published': form.is_published.data,
                'author_id': current_user.id,
                'image_filename': cover_image_filename,  # cover_image -> image_filename
                'thumbnail_filename': thumbnail_filename,  # 썸네일 파일명 추가
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
            # Handle file upload
            current_app.logger.info(f'Edit Post - Form data: {request.form}')
            current_app.logger.info(f'Edit Post - Files received: {request.files}')
            
            # 이미지 파일 처리
            current_app.logger.info('Edit Post - Checking for uploaded files...')
            image = request.files.get('image')
            cover_image_filename = post.image_filename
            thumbnail_filename = post.thumbnail_filename if hasattr(post, 'thumbnail_filename') else None
            
            # 요청의 모든 파일 정보 로깅
            current_app.logger.info(f'Edit Post - Request files: {request.files}')
            current_app.logger.info(f'Edit Post - Request form data: {request.form}')
            current_app.logger.info(f'Edit Post - Request headers: {dict(request.headers)}')
            
            if image and hasattr(image, 'filename') and image.filename:
                current_app.logger.info(f'Edit Post - Image object: {image}')
                current_app.logger.info(f'Edit Post - Image filename: {image.filename}, Content-Type: {image.content_type}, Content-Length: {image.content_length if hasattr(image, "content_length") else "N/A"}')
                
                # 파일이 비어있는지 확인
                if not image.filename.strip():
                    current_app.logger.warning('Edit Post - No filename provided or filename is empty')
                    flash('파일을 선택해주세요.', 'warning')
                
                # 파일 포인터를 처음으로 되돌림
                if hasattr(image, 'seek'):
                    image.seek(0, 2)  # 파일 끝으로 이동
                    file_size = image.tell()
                    image.seek(0)  # 다시 파일 시작으로 되돌림
                    current_app.logger.info(f'Edit Post - Actual file size from stream: {file_size} bytes')
                    
                    if file_size == 0:
                        error_msg = '업로드된 파일이 비어 있습니다.'
                        current_app.logger.warning(f'Edit Post - {error_msg}')
                        flash(error_msg, 'danger')
                        return render_template('admin/edit_post.html', title='글 수정', form=form, post=post, current_user=current_user)
                
                # 파일 크기 확인 (최대 10MB)
                max_size = 10 * 1024 * 1024  # 10MB
                if hasattr(image, 'content_length') and image.content_length > max_size:
                    error_msg = '파일 크기가 너무 큽니다. 10MB 이하의 파일만 업로드 가능합니다.'
                    current_app.logger.warning(f'Edit Post - {error_msg}')
                    flash(error_msg, 'danger')
                    return render_template('admin/edit_post.html', title='글 수정', form=form, post=post, current_user=current_user)
                
                # 파일 확장자 확인
                if '.' not in image.filename:
                    current_app.logger.warning(f'Edit Post - Invalid filename (no extension): {image.filename}')
                    flash('유효하지 않은 파일 이름입니다. 확장자가 포함되어야 합니다.', 'warning')
                    return render_template('admin/edit_post.html', title='글 수정', form=form, post=post, current_user=current_user)
                
                if not allowed_file(image.filename):
                    error_msg = f'허용되지 않는 파일 형식입니다: {image.filename}. 허용되는 형식: {ALLOWED_EXTENSIONS}'
                    current_app.logger.warning(f'Edit Post - {error_msg}')
                    flash(error_msg, 'danger')
                    return render_template('admin/edit_post.html', title='글 수정', form=form, post=post, current_user=current_user)
                
                try:
                    current_app.logger.info('Edit Post - Attempting to save new image...')
                    
                    # 기존 이미지 삭제
                    if post.image_filename:
                        current_app.logger.info(f'Edit Post - Deleting old image: {post.image_filename}')
                        result = delete_cover_image(post.image_filename)
                        if not result['success']:
                            current_app.logger.error(f"Edit Post - Error deleting old images: {result.get('error', 'Unknown error')}")
                        else:
                            current_app.logger.info(f"Edit Post - Deleted {len(result['deleted_files'])} files: {', '.join(result['deleted_files'])}")
                    
                    # 새 이미지 저장
                    image_filename, thumbnail_filename = save_cover_image(image)
                    cover_image_filename = image_filename
                    current_app.logger.info(f'Edit Post - Image saved successfully: {image_filename}, Thumbnail: {thumbnail_filename}')
                except Exception as e:
                    current_app.logger.error(f'Edit Post - Error saving image: {str(e)}', exc_info=True)
                    flash(f'이미지 저장 중 오류가 발생했습니다: {str(e)}', 'danger')
                    return render_template('admin/edit_post.html', title='글 수정', form=form, post=post, current_user=current_user)
            else:
                current_app.logger.info('Edit Post - No new image file was uploaded, keeping existing one')
                if not image:
                    current_app.logger.info('Edit Post - No image field in request')
                elif not hasattr(image, 'filename'):
                    current_app.logger.info('Edit Post - Image field has no filename attribute')
                elif not image.filename:
                    current_app.logger.info('Edit Post - Image filename is empty')
                
                # 이미지가 없으면 기존 이미지 유지
                if image and hasattr(image, 'filename') and image.filename:
                    try:
                        # Delete old cover image if exists
                        if post.image_filename:
                            current_app.logger.info(f'Deleting old image: {post.image_filename}')
                            delete_cover_image(post.image_filename)
                        
                        # Save new cover image
                        current_app.logger.info('Saving new cover image...')
                        image_filename, thumbnail_filename = save_cover_image(image)
                        current_app.logger.info(f'New image saved successfully. Filename: {image_filename}, Thumbnail: {thumbnail_filename}')
                        cover_image_filename = image_filename
                    except Exception as e:
                        current_app.logger.error(f'Error updating cover image: {e}')
                        flash('커버 이미지 업데이트 중 오류가 발생했습니다.', 'danger')
                        return render_template('admin/edit_post.html', 
                                             title='글 수정',
                                             form=form, 
                                             post=post,
                                             current_user=current_user)
                else:
                    # 이미지가 없으면 기존 이미지 유지
                    cover_image_filename = post.image_filename
                    thumbnail_filename = post.thumbnail_filename if hasattr(post, 'thumbnail_filename') else None
                    current_app.logger.info('No new image provided, keeping existing image')
            
            # Handle publishing status
            is_published = post.is_published
            published_at = post.published_at
            
            # 게시 상태 변경 처리
            if 'save_draft' in request.form and request.form['save_draft'] == 'true':
                # 초안 저장 버튼 클릭 시
                is_published = False
                current_app.logger.info("게시물 상태: 초안으로 저장")
            elif 'publish' in request.form and request.form['publish'] == 'true':
                # 발행 버튼 클릭 시
                is_published = True
                if not post.published_at:  # 처음 발행되는 경우에만 발행일 업데이트
                    published_at = datetime.utcnow()
                current_app.logger.info("게시물 상태: 발행됨")
            elif 'unpublish' in request.form and request.form['unpublish'] == 'true':
                # 발행 취소 버튼 클릭 시
                is_published = False
                current_app.logger.info("게시물 상태: 초안으로 변경")
            
            # Prepare update data
            update_data = {
                'title': form.title.data,
                'content': form.content.data,
                'excerpt': form.excerpt.data or None,
                'is_published': is_published,
                'published_at': published_at,
                'meta_title': form.meta_title.data or None,
                'meta_description': form.meta_description.data or None,
                'category_id': int(form.category.data) if form.category.data and int(form.category.data) > 0 else None,
                'tags': form.tags.data if isinstance(form.tags.data, list) else (form.tags.data.split(',') if form.tags.data else []),
                'image_filename': cover_image_filename,
                'thumbnail_filename': thumbnail_filename
            }
            
            # 서비스 레이어를 사용하여 포스트 업데이트
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
