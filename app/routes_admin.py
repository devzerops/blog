from flask import (
    Blueprint, render_template, redirect, url_for, 
    request, flash, current_app, send_from_directory, jsonify, session, Response, abort, send_file, make_response
)
from app.auth import token_required, admin_required # Keep for reference if needed, but new logic below
from app.models import Post, User, Comment, PageView, SiteSetting, Category # Tag model not used, tags are stored as comma-separated strings
from app.forms import PostForm, SettingsForm, DeleteForm, ImportForm, SiteSettingsForm, CategoryForm # Added SiteSettingsForm, CategoryForm
from app.database import db
from werkzeug.utils import secure_filename
import os
# import markdown # Not needed for admin routes directly, but for public display
from datetime import datetime, timezone, timedelta # Added timedelta, timezone
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, URLField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, URL as URLValidator # Renamed to avoid conflict
from flask_wtf.file import FileAllowed
import re
from PIL import Image # Import Pillow Image
# from slugify import slugify # Removed slugify as it's no longer used
import json # For creating the JSON structure
import jwt # For decoding token
import zipfile
import tempfile
import os
import shutil
from sqlalchemy import func # Added func

bp_admin = Blueprint('admin', __name__)

# Use the admin_required decorator from auth.py
# No need to redefine it here as it's already imported at the top

def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def optimize_image(image_path, max_width=1200, quality=85):
    """Optimizes an image by resizing and compressing it."""
    try:
        img = Image.open(image_path)
        img_format = img.format

        # Resize if wider than max_width, maintaining aspect ratio
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save with optimization
        if img_format in ['JPEG', 'JPG']:
            img.save(image_path, format='JPEG', quality=quality, optimize=True)
        elif img_format == 'PNG':
            img.save(image_path, format='PNG', optimize=True)
        else:
            # For other formats like GIF, just save without specific optimization for now
            # or convert to a more common format if desired.
            img.save(image_path, format=img_format)
        
        current_app.logger.info(f"Optimized image saved at {image_path}")
    except Exception as e:
        current_app.logger.error(f"Error optimizing image {image_path}: {e}")

@bp_admin.route('/dashboard')
@bp_admin.route('/') # Make dashboard the default for /admin/
@token_required
def dashboard(current_user):
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(user_id=current_user.id).order_by(Post.updated_at.desc()).paginate(
        page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 10), error_out=False
    )
    posts = posts_pagination.items
    return render_template('admin_dashboard.html', title='관리자 대시보드', posts=posts, pagination=posts_pagination, current_user=current_user)

@bp_admin.route('/posts', methods=['GET'])
@admin_required
def admin_posts(current_user):
    page = request.args.get('page', 1, type=int)
    # Assuming you have a way to get posts_per_page, e.g., from SiteSettings or config
    # For now, using a default or a value from app.config
    posts_per_page = current_app.config.get('POSTS_PER_PAGE_ADMIN', 10) 
    query = Post.query.order_by(Post.pub_date.desc())
    pagination = query.paginate(page=page, per_page=posts_per_page, error_out=False)
    posts = pagination.items
    return render_template('admin/admin_posts_list.html', 
                           posts=posts, 
                           pagination=pagination, 
                           title='Manage Posts', 
                           current_user=current_user)

@bp_admin.route('/post/new', methods=['GET', 'POST'])
@admin_required
def new_post(current_user):
    form = PostForm()
    # 폼 제출 및 검증 디버깅
    if request.method == 'POST':
        current_app.logger.info(f"POST 요청 받음: {request.form.keys()}")
        current_app.logger.info(f"content 필드 값: {request.form.get('content')[:100] if request.form.get('content') else 'None'}")
        current_app.logger.info(f"title 필드 값: {request.form.get('title')[:100] if request.form.get('title') else 'None'}")
        
        # 폼 검증 오류 로깅
        if not form.validate_on_submit():
            for field, errors in form.errors.items():
                current_app.logger.error(f"Field {field} failed validation with errors: {errors}")
            return render_template('edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)
    
    # 폼 검증 성공
    if form.validate_on_submit():
        # Handle cover image upload and optimization
        cover_image_filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(filepath)
            # Optimize image
            optimized_filepath = optimize_image(filepath)
            cover_image_filename = os.path.basename(optimized_filepath) # Save only the filename

        # Determine if post should be published based on which button was clicked
        is_published = False
        published_at = None
        
        # Check which submit button was clicked
        if 'publish' in request.form:
            # If publish button was clicked, always set as published
            is_published = True
            published_at = datetime.utcnow()
        elif 'save_draft' in request.form:
            # If save_draft button was clicked, always set as draft
            is_published = False
        else:
            # Fallback to form data (shouldn't happen with current form design)
            is_published = form.is_published.data
            if is_published:
                published_at = datetime.utcnow()
                
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id, 
            image_filename=cover_image_filename, # Using the cover_image_filename variable but assigning to image_filename field
            alt_text=form.alt_text.data, 
            video_embed_url=form.video_embed_url.data, 
            is_published=is_published,
            published_at=published_at,
            category_id=form.category.data.id if form.category.data else None
        )

        db.session.add(post)
        db.session.commit()

        # Assign tags directly as a comma-separated string
        post.tags = form.tags.data
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('edit_post.html', title='New Post', form=form, legend='New Post', current_user=current_user)

@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(current_user, post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)

    if form.validate_on_submit():
        # Handle cover image upload and optimization
        if form.image.data:
            # If there's an old image and a new one is uploaded, delete the old one
            if post.image_filename: # Changed from cover_image_filename
                old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.cover_image_filename)
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except OSError as e:
                        flash(f'Error deleting old cover image: {e}', 'warning')
            
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(filepath)
            optimized_filepath = optimize_image(filepath)
            post.image_filename = os.path.basename(optimized_filepath) # Changed from cover_image_filename

        post.title = form.title.data
        post.content = form.content.data
        post.alt_text = form.alt_text.data # Changed from cover_image_alt_text
        post.video_embed_url = form.video_embed_url.data # Changed from video_url
        post.category_id = form.category.data.id if form.category.data else None # Update category ID

        # Check which submit button was clicked
        if 'publish' in request.form:
            # If publish button was clicked, always set as published
            post.is_published = True
            if not post.published_at:  # If it wasn't published before
                post.published_at = datetime.utcnow()
        elif 'save_draft' in request.form:
            # If save_draft button was clicked, always set as draft
            post.is_published = False
            post.published_at = None
        else:
            # Fallback to form data (shouldn't happen with current form design)
            if form.is_published.data and not post.is_published:
                post.published_at = datetime.utcnow()
            elif not form.is_published.data:
                post.published_at = None
            post.is_published = form.is_published.data

        post.updated_at = datetime.utcnow()

        # Assign tags directly as a comma-separated string
        post.tags = form.tags.data

        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    elif request.method == 'GET':
        # Populate form with existing category if available
        if post.category_id:
            form.category.data = Category.query.get(post.category_id)
        # Populate tags for GET request (already handled by obj=post for other fields)
        form.tags.data = post.tags

    return render_template('edit_post.html', title='Edit Post', form=form, post=post, legend=f'Edit "{post.title}"', current_user=current_user)

@bp_admin.route('/post/delete/<int:post_id>', methods=['POST'])
@token_required
def delete_post(current_user, post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if post.cover_image_filename:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.cover_image_filename)
        if os.path.exists(image_path):
            try: os.remove(image_path)
            except OSError as e: current_app.logger.error(f"Error deleting image {image_path}: {e}")

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# Serves uploaded files from the UPLOAD_FOLDER (defined in config.py)
@bp_admin.route('/uploads/<path:filename>') # Use <path:filename> for subdirectories if ever needed
@token_required # Or make it public if images are directly linked in public posts
def uploaded_file(current_user, filename):
    # Security: Ensure this only serves files from the designated UPLOAD_FOLDER
    # and potentially check if the current_user has rights to this file if it's not public.
    # For now, assuming admin access implies access to all uploaded files for management.
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# For rich text editor image uploads (e.g., TinyMCE, CKEditor)
@bp_admin.route('/upload_editor_image', methods=['POST'])
@token_required
def upload_editor_image(current_user):
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'No file part in the request'}}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': {'message': 'No file selected for uploading'}}), 400
    
    if file and _allowed_file(file.filename):
        s_filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{s_filename}"
        try:
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            optimize_image(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)) # Optimize the saved image
            # The URL returned should be accessible by the editor to display the image.
            # If UPLOAD_FOLDER is under static, url_for can generate it.
            # If it's outside static, you'll need a dedicated route like uploaded_file.
            # Assuming UPLOAD_FOLDER is 'app/static/uploads' as per original plan.
            # The 'admin.uploaded_file' route needs to be accessible without token if images are public.
            # For now, let's assume it's okay for admin to see it via this route.
            image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
            return jsonify({'location': image_url})
        except Exception as e:
            current_app.logger.error(f"Editor image upload error: {e}")
            return jsonify({'error': {'message': f'Image upload failed: {e}'}}), 500
    else:
        return jsonify({'error': {'message': 'File type not allowed'}}), 400

# Content Export Route
@bp_admin.route('/export/all_content', methods=['GET'])
@admin_required
def export_all_content(current_user): # Re-added current_user argument
    try:
        # 1. Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        images_temp_dir = os.path.join(temp_dir, 'images')
        os.makedirs(images_temp_dir, exist_ok=True)

        all_posts = Post.query.order_by(Post.created_at.asc()).all()
        all_comments = Comment.query.order_by(Comment.created_at.asc()).all()

        posts_data = []
        for post in all_posts:
            relative_image_path = None
            if post.image_filename: # Changed from cover_image_filename
                original_image_relative_path = post.cover_image_filename
                image_filename_only = os.path.basename(original_image_relative_path)
                source_image_path_in_zip = os.path.join(current_app.static_folder, 'uploads', image_filename_only)
                if os.path.exists(source_image_path_in_zip):
                    # Copy image to temp dir
                    shutil.copy(source_image_path_in_zip, images_temp_dir)
                    relative_image_path = f'images/{post.cover_image_filename}' # Path within the zip
            
            post_item = {
                'id': post.id,
                'title': post.title,
                'content': post.content, 
                'created_at': post.created_at.isoformat() + 'Z' if post.created_at else None,
                'updated_at': post.updated_at.isoformat() + 'Z' if post.updated_at else None,
                'is_published': post.is_published,
                'published_at': post.published_at.isoformat() + 'Z' if post.published_at else None,
                'featured_image_url': relative_image_path, # Updated to relative path
                'tags': post.tags, 
                'meta_description': post.meta_description,
                'slug': getattr(post, 'slug', None) 
            }
            posts_data.append(post_item)

        comments_data = []
        for comment in all_comments:
            comment_item = {
                'id': comment.id,
                'nickname': comment.nickname,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
                'post_original_id': comment.post_id, # Assuming this links to the original post's ID
                'ip_address': str(comment.ip_address) if comment.ip_address else None, # Ensure IP is string
                'parent_original_id': comment.parent_id # Assuming this links to the original parent comment's ID
            }
            comments_data.append(comment_item)

        export_data = {
            'posts': posts_data,
            'comments': comments_data
        }

        # 2. Save JSON to temp dir
        json_filename = 'blog_export.json'
        json_temp_path = os.path.join(temp_dir, json_filename)
        with open(json_temp_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)

        # 3. Create ZIP archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename_on_server = f'blog_export_{timestamp}.zip'
        zip_temp_path = os.path.join(tempfile.gettempdir(), zip_filename_on_server) # Store zip in system temp for sending
        
        with zipfile.ZipFile(zip_temp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add JSON file to zip
            zf.write(json_temp_path, arcname=json_filename)
            # Add images to zip
            for root, _, files in os.walk(images_temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('images', file) # Store images in 'images/' folder in zip
                    zf.write(file_path, arcname=arcname)

        # 4. Send the ZIP file and then clean up
        response = send_file(zip_temp_path, as_attachment=True, download_name=zip_filename_on_server)
        
        # 5. Clean up: This should ideally be done after the response is sent.
        # Flask's `after_this_request` can be used, or a try/finally block if `send_file` is blocking.
        # For simplicity here, we'll clean up directly. If send_file is non-blocking, this might be too soon.
        # However, send_file is typically blocking for file objects.
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting content as ZIP: {e}")
        flash('콘텐츠를 ZIP으로 내보내는 중 오류가 발생했습니다.', 'danger')
        return redirect(url_for('admin.dashboard'))
    finally:
        # Ensure temporary directory is always cleaned up
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        # Clean up the zip file from system temp if it exists (in case of error before send_file)
        if 'zip_temp_path' in locals() and os.path.exists(zip_temp_path) and not 'response' in locals():
             os.remove(zip_temp_path)

@bp_admin.route('/data/restore', methods=['GET', 'POST']) # Changed route and name
@admin_required
def data_restore(current_user): # Renamed function, current_user is used here
    form = ImportForm()
    if form.validate_on_submit(): # This handles POST requests
        if 'backup_file' not in request.files:
            flash('백업 파일이 없습니다.', 'danger')
            return redirect(url_for('admin.data_restore')) # Corrected redirect

        file = request.files['backup_file']
        if file.filename == '':
            flash('선택된 파일이 없습니다.', 'danger')
            return redirect(url_for('admin.data_restore')) # Corrected redirect

        if file and file.filename.endswith('.zip'):
            upload_temp_dir = None
            try:
                temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                file.save(temp_zip_file.name)
                temp_zip_file.close()

                upload_temp_dir = tempfile.mkdtemp()

                with zipfile.ZipFile(temp_zip_file.name, 'r') as zip_ref:
                    zip_ref.extractall(upload_temp_dir)
                
                json_path = os.path.join(upload_temp_dir, 'blog_export.json')
                if not os.path.exists(json_path):
                    flash('백업 파일에 blog_export.json 파일이 없습니다.', 'danger')
                    # No need to raise FileNotFoundError, flash and redirect is enough
                    return redirect(url_for('admin.data_restore')) # Corrected redirect

                with open(json_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                current_app.logger.info(f"Successfully read backup data. Posts: {len(backup_data.get('posts', []))}, Comments: {len(backup_data.get('comments', []))}")
                # flash('백업 파일을 성공적으로 읽었습니다. 복원 처리를 시작합니다.', 'info') # Keep user informed
                
                original_post_id_to_new_id_map = {}
                if 'posts' in backup_data:
                    for post_data in backup_data['posts']:
                        new_image_filename = None
                        if post_data.get('featured_image_url'):
                            original_image_relative_path = post_data['featured_image_url']
                            image_filename_only = os.path.basename(original_image_relative_path)
                            source_image_path_in_zip = os.path.join(upload_temp_dir, 'images', image_filename_only)
                            if os.path.exists(source_image_path_in_zip):
                                fn, ext = os.path.splitext(image_filename_only)
                                timestamp_suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
                                new_image_filename = f"{fn}_{timestamp_suffix}{ext}"
                                destination_image_path = os.path.join(current_app.static_folder, 'uploads', new_image_filename)
                                os.makedirs(os.path.join(current_app.static_folder, 'uploads'), exist_ok=True)
                                shutil.copy(source_image_path_in_zip, destination_image_path)
                            else:
                                current_app.logger.warning(f"Image {image_filename_only} referenced but not found.")

                        created_at_dt = datetime.fromisoformat(post_data['created_at'].replace('Z', '')) if post_data.get('created_at') else None
                        updated_at_dt = datetime.fromisoformat(post_data['updated_at'].replace('Z', '')) if post_data.get('updated_at') else None
                        published_at_dt = datetime.fromisoformat(post_data['published_at'].replace('Z', '')) if post_data.get('published_at') else None

                        new_post = Post(
                            title=post_data.get('title'),
                            content=post_data.get('content'),
                            created_at=created_at_dt,
                            updated_at=updated_at_dt,
                            is_published=post_data.get('is_published', False),
                            published_at=published_at_dt,
                            cover_image_filename=new_image_filename,
                            tags=post_data.get('tags'),
                            meta_description=post_data.get('meta_description'),
                            slug=post_data.get('slug'),
                            user_id=current_user.id
                        )
                        db.session.add(new_post)
                        db.session.flush()
                        if post_data.get('id'):
                            original_post_id_to_new_id_map[str(post_data['id'])] = new_post.id
            
                original_comment_id_to_new_id_map = {}
                comments_to_update_parent_id = []
                if 'comments' in backup_data:
                    for comment_data in backup_data['comments']:
                        original_post_id_str = str(comment_data.get('post_original_id'))
                        new_post_id = original_post_id_to_new_id_map.get(original_post_id_str)
                        if not new_post_id:
                            current_app.logger.warning(f"Comment (orig ID: {comment_data.get('id')}) refs unmapped post (orig ID: {original_post_id_str}). Skipping.")
                            continue
                        created_at_dt = datetime.fromisoformat(comment_data['created_at'].replace('Z', '')) if comment_data.get('created_at') else datetime.utcnow()
                        new_comment = Comment(
                            nickname=comment_data.get('nickname'),
                            content=comment_data.get('content'),
                            created_at=created_at_dt,
                            post_id=new_post_id
                        )
                        db.session.add(new_comment)
                        db.session.flush()
                        original_comment_id_str = str(comment_data.get('id'))
                        if original_comment_id_str:
                            original_comment_id_to_new_id_map[original_comment_id_str] = new_comment.id
                        original_parent_id_str = str(comment_data.get('parent_original_id'))
                        if original_parent_id_str and original_parent_id_str != 'None':
                            comments_to_update_parent_id.append({'comment_obj': new_comment, 'original_parent_id': original_parent_id_str})
            
                for item in comments_to_update_parent_id:
                    comment_to_update = item['comment_obj']
                    original_parent_id_str = item['original_parent_id']
                    new_parent_id = original_comment_id_to_new_id_map.get(original_parent_id_str)
                    if new_parent_id:
                        comment_to_update.parent_id = new_parent_id
                    else:
                        current_app.logger.warning(f"Could not find new parent ID for comment (new ID: {comment_to_update.id}) with original parent ID {original_parent_id_str}.")
            
                db.session.commit()
                flash('콘텐츠 복원이 완료되었습니다 (게시물 및 댓글).', 'success')
                current_app.logger.info(f"Post ID map: {original_post_id_to_new_id_map}")
                current_app.logger.info(f"Comment ID map: {original_comment_id_to_new_id_map}")
                return redirect(url_for('admin.dashboard')) # Redirect to main dashboard after successful import

            except Exception as e: # Catch more general exceptions after specific ones if any
                current_app.logger.error(f"Error importing content from ZIP: {e}")
                flash(f'콘텐츠를 ZIP에서 가져오는 중 오류가 발생했습니다: {e}', 'danger')
                db.session.rollback() # Rollback on error
                return redirect(url_for('admin.data_restore')) # Corrected redirect
            finally:
                if 'temp_zip_file' in locals() and os.path.exists(temp_zip_file.name):
                    os.remove(temp_zip_file.name)
                if upload_temp_dir and os.path.exists(upload_temp_dir):
                    shutil.rmtree(upload_temp_dir)
        else: # if not (file and file.filename.endswith('.zip'))
            flash('잘못된 파일 형식입니다. ZIP 파일을 업로드해주세요.', 'danger')
            return redirect(url_for('admin.data_restore')) # Corrected redirect

    elif request.method == 'POST':
        flash('파일 업로드 중 오류가 발생했습니다. 파일을 확인해주세요.', 'danger')
    
    return render_template('admin_data_restore.html', title='데이터 복원', import_form=form)

@bp_admin.route('/site-stats')
@admin_required
def site_stats(current_user):
    today_start_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_views_today = db.session.query(func.count(PageView.id)).filter(PageView.timestamp >= today_start_utc).scalar()
    total_comments_today = db.session.query(func.count(Comment.id)).filter(Comment.created_at >= today_start_utc).scalar()

    # For 'currently active users' - this is a placeholder. 
    # Real active user tracking is more complex (e.g., using sessions with last_seen timestamps or Redis).
    # For now, we can show the number of unique IPs that viewed pages in the last 5 minutes as a proxy.
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    active_users_approx = db.session.query(func.count(func.distinct(PageView.ip_address)))\
                                  .filter(PageView.timestamp >= five_minutes_ago).scalar()

    return render_template('admin_site_stats.html', 
                           title='사이트 통계',
                           total_views_today=total_views_today,
                           total_comments_today=total_comments_today,
                           active_users_approx=active_users_approx,
                           current_user=current_user)

@bp_admin.route('/profile-settings', methods=['GET', 'POST'])
@admin_required
def profile_settings(current_user_from_token):
    # This form is for User model attributes like username, password
    form = SettingsForm(original_username=current_user_from_token.username, obj=current_user_from_token) 
    if form.validate_on_submit():
        # Handle password change
        if form.new_password.data:
            if not form.current_password.data:
                flash('새 비밀번호를 설정하려면 현재 비밀번호를 입력해야 합니다.', 'danger')
                return render_template('admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)
            if not current_user_from_token.check_password(form.current_password.data):
                flash('현재 비밀번호가 정확하지 않습니다.', 'danger')
                return render_template('admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)
            current_user_from_token.set_password(form.new_password.data)
            flash('비밀번호가 성공적으로 변경되었습니다.', 'info')

        # Handle username change
        if current_user_from_token.username != form.username.data:
            # Form's validate_username should handle uniqueness check if username.data != original_username
            current_user_from_token.username = form.username.data
            flash('사용자 아이디가 성공적으로 변경되었습니다.', 'info')
        
        db.session.add(current_user_from_token)
        db.session.commit()
        flash('관리자 프로필 설정이 성공적으로 저장되었습니다.', 'success')
        return redirect(url_for('admin.profile_settings')) # Redirect to the new URL
    
    # For GET request, populate form fields that are not directly mapped by obj if necessary
    # Example: form.username.data = current_user_from_token.username (already handled by obj)

    return render_template('admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)

@bp_admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def site_settings(current_user): # current_user is passed by @admin_required
    settings_obj = SiteSetting.query.first()
    if not settings_obj:
        settings_obj = SiteSetting()
        db.session.add(settings_obj)
        try:
            db.session.commit()
            flash('사이트 설정이 초기화되었습니다. 기본값을 검토하고 저장해주세요.', 'info')
            settings_obj = SiteSetting.query.first() # Re-fetch to get ID and ensure it's managed by session
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating initial site settings: {e}")
            flash('초기 사이트 설정을 생성하는 중 오류가 발생했습니다.', 'danger')
            return redirect(url_for('admin.dashboard')) # Or some other safe place

    form = SiteSettingsForm(obj=settings_obj)

    if form.validate_on_submit():
        # Handle favicon upload first
        if form.favicon_file.data:
            file = form.favicon_file.data
            filename = secure_filename(file.filename)
            favicon_folder = os.path.join(current_app.static_folder, 'img', 'favicon')
            os.makedirs(favicon_folder, exist_ok=True)

            # Delete old favicon if it exists and is different
            if settings_obj.favicon_filename and settings_obj.favicon_filename != filename:
                old_favicon_path = os.path.join(favicon_folder, settings_obj.favicon_filename)
                if os.path.exists(old_favicon_path):
                    try:
                        os.remove(old_favicon_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old favicon {old_favicon_path}: {e}")
            
            try:
                file.save(os.path.join(favicon_folder, filename))
                settings_obj.favicon_filename = filename
            except Exception as e:
                flash(f'파비콘 파일 저장 중 오류 발생: {e}', 'danger')
                current_app.logger.error(f"Favicon save error: {e}")

        # Populate other form data to the object
        # Need to exclude favicon_file as it's not a direct model field
        form_data_dict = form.data.copy()
        form_data_dict.pop('favicon_file', None) # Remove file field from dict before populating
        form_data_dict.pop('csrf_token', None) # CSRF token is not part of the model
        form_data_dict.pop('submit', None) # Submit button is not part of the model

        for key, value in form_data_dict.items():
            if hasattr(settings_obj, key):
                setattr(settings_obj, key, value)

        try:
            db.session.commit()
            flash('사이트 설정이 성공적으로 저장되었습니다.', 'success')
            return redirect(url_for('admin.site_settings')) # Redirect to the same page
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving site settings: {e}")
            flash(f'사이트 설정 저장 중 오류 발생: {e}', 'danger')

    # For GET request, if there's a favicon_filename, ensure form.favicon_file.data is not incorrectly populated
    # This is generally not an issue as FileField is not populated from obj like other fields.

    return render_template('admin/settings.html', title='사이트 설정', form=form, current_user=current_user)

# Category Management
@bp_admin.route('/categories', methods=['GET'])
@admin_required
def admin_categories(current_user):
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/admin_categories_list.html', categories=categories, title='Manage Categories', current_user=current_user)

@bp_admin.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def admin_new_category(current_user):
    form = CategoryForm()
    if form.validate_on_submit():
        category_name = form.name.data
        existing_category = Category.query.filter_by(name=category_name).first()
        if existing_category:
            flash('Category with this name already exists.', 'warning')
        else:
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully.', 'success')
            return redirect(url_for('admin.admin_categories'))
    return render_template('admin/admin_category_form.html', form=form, title='Add New Category', legend='New Category', current_user=current_user)

@bp_admin.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(current_user, category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category_name = form.name.data
        # Check if another category with the new name already exists (excluding the current one)
        existing_category = Category.query.filter(Category.name == category_name, Category.id != category_id).first()
        if existing_category:
            flash('Another category with this name already exists.', 'warning')
        else:
            category.name = category_name
            db.session.commit()
            flash('Category updated successfully.', 'success')
            return redirect(url_for('admin.admin_categories'))
    return render_template('admin/admin_category_form.html', form=form, title='Edit Category', legend=f'Edit {category.name}', category=category, current_user=current_user)

@bp_admin.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(current_user, category_id):
    category = Category.query.get_or_404(category_id)
    if category.posts.count() > 0:
        flash('Cannot delete category. It is associated with one or more posts. Please reassign posts before deleting.', 'danger')
        return redirect(url_for('admin.admin_categories'))
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.admin_categories'))

# Tag Management (existing code) - Commenting out as Tag model is now a string field on Post
# @bp_admin.route('/tags', methods=['GET'])
# @admin_required
# def admin_tags(current_user):
#     tags = Tag.query.order_by(Tag.name).all()
#     return render_template('admin/admin_tags_list.html', tags=tags, title='Manage Tags', current_user=current_user)
# 
# @bp_admin.route('/tags/new', methods=['GET', 'POST'])
# @admin_required
# def add_tag(current_user):
#     form = TagForm()
#     if form.validate_on_submit():
#         tag_name = form.name.data
#         existing_tag = Tag.query.filter_by(name=tag_name).first()
#         if existing_tag:
#             flash('Tag with this name already exists.', 'warning')
#         else:
#             new_tag = Tag(name=tag_name)
#             db.session.add(new_tag)
#             db.session.commit()
#             flash('Tag added successfully.', 'success')
#             return redirect(url_for('admin.admin_tags'))
#     return render_template('admin/admin_tag_form.html', form=form, title='Add New Tag', legend='New Tag', current_user=current_user)
# 
# @bp_admin.route('/tags/edit/<int:tag_id>', methods=['GET', 'POST'])
# @admin_required
# def edit_tag(current_user, tag_id):
#     tag = Tag.query.get_or_404(tag_id)
#     form = TagForm(obj=tag)
#     if form.validate_on_submit():
#         tag_name = form.name.data
#         # Check if another tag with the new name already exists (excluding the current one)
#         existing_tag = Tag.query.filter(Tag.name == tag_name, Tag.id != tag_id).first()
#         if existing_tag:
#             flash('Another tag with this name already exists.', 'warning')
#         else:
#             tag.name = tag_name
#             db.session.commit()
#             flash('Tag updated successfully.', 'success')
#             return redirect(url_for('admin.admin_tags'))
#     return render_template('admin/admin_tag_form.html', form=form, title='Edit Tag', legend=f'Edit {tag.name}', tag=tag, current_user=current_user)
# 
# @bp_admin.route('/tags/delete/<int:tag_id>', methods=['POST'])
# @admin_required
# def delete_tag(current_user, tag_id):
#     tag = Tag.query.get_or_404(tag_id)
#     if tag.posts.count() > 0:
#         flash('Cannot delete tag. It is associated with one or more posts. Please reassign posts before deleting.', 'danger')
#         return redirect(url_for('admin.admin_tags'))
#     db.session.delete(tag)
#     db.session.commit()
#     flash('Tag deleted successfully.', 'success')
#     return redirect(url_for('admin.admin_tags'))
