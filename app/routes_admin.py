from flask import (
    Blueprint, render_template, redirect, url_for, 
    request, flash, current_app, send_from_directory, jsonify, session, Response, abort, send_file
)
from app.auth import token_required # Keep for reference if needed, but new logic below
from app.models import Post, User, Comment # Removed Tag, Added User, Comment
from app.forms import PostForm, SettingsForm, DeleteForm # Removed TagForm
from app.database import db
from werkzeug.utils import secure_filename
import os
# import markdown # Not needed for admin routes directly, but for public display
from datetime import datetime, timezone
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

bp_admin = Blueprint('admin', __name__)

# Decorator to check if user is admin
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('admin_token')
        if not token:
            flash('로그인이 필요합니다. 이 페이지에 접근하려면 먼저 로그인해주세요.', 'warning')
            return redirect(url_for('auth.login_page', next=request.url))
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                raise jwt.InvalidTokenError("User not found.")

            # Check if the current user is the admin
            # Uses ADMIN_USERNAME from config, defaults to 'admin'
            admin_username = current_app.config.get('ADMIN_USERNAME', 'admin')
            if current_user.username != admin_username:
                flash('이 작업을 수행하려면 관리자 권한이 필요합니다.', 'danger')
                return redirect(url_for('public.post_list')) 

        except jwt.ExpiredSignatureError:
            flash('세션이 만료되었습니다. 다시 로그인해주세요.', 'warning')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page', next=request.url))
        except jwt.InvalidTokenError as e:
            flash(f'유효하지 않은 토큰이거나 사용자 정보 오류입니다: {e}', 'danger')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            current_app.logger.error(f"Admin Auth Error: {e}")
            flash('인증 중 오류가 발생했습니다.', 'danger')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page'))
        
        # Pass current_user to the decorated function if it accepts it
        # This mimics how token_required might pass current_user
        # Check if 'current_user' is in the function's arguments
        import inspect
        sig = inspect.signature(f)
        if 'current_user' in sig.parameters:
            return f(current_user, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated_function

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=1, max=140)])
    content = TextAreaField('내용 (Markdown 지원)') 
    image = FileField('커버 이미지 (선택)', validators=[
        Optional(), 
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '이미지 파일(jpg, jpeg, png, gif)만 업로드 가능합니다!')
    ])
    alt_text = StringField('이미지 설명 (Alt Text)', validators=[Optional(), Length(max=255)]) # New field
    video_embed_url = URLField('동영상 URL (선택, 예: YouTube)', validators=[Optional(), URLValidator()])
    meta_description = StringField('메타 설명 (선택)', validators=[Optional(), Length(max=255)]) # New field
    tags = StringField('태그 (쉼표로 구분)')
    submit = SubmitField('저장') # Changed from '발행' for consistency

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

@bp_admin.route('/post/new', methods=['GET', 'POST'])
@token_required
def new_post(current_user):
    form = PostForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            file = form.image.data
            if _allowed_file(file.filename):
                s_filename = secure_filename(file.filename)
                filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{s_filename}"
                try:
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    optimize_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    flash(f'이미지 저장 중 오류 발생: {e}', 'danger')
                    current_app.logger.error(f"Image save error: {e}")
                    filename = None
            else:
                flash('허용되지 않는 이미지 파일 형식입니다.', 'warning')

        # Determine if publishing or saving as draft
        if 'publish' in request.form:
            is_currently_published = True
            current_published_at = datetime.now(timezone.utc)
            flash_message = '새로운 글이 성공적으로 발행되었습니다!'
        else: # Default to saving as draft if 'publish' is not in form (e.g. 'save_draft' was clicked)
            is_currently_published = False
            current_published_at = None
            flash_message = '글이 임시 저장되었습니다.'

        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            image_filename=filename if filename else None,
            alt_text=form.alt_text.data,
            video_embed_url=form.video_embed_url.data,
            meta_description=form.meta_description.data,
            is_published=is_currently_published,
            published_at=current_published_at,
            tags=form.tags.data
        )

        db.session.add(post)
        db.session.commit()
        flash(flash_message, 'success')
        return redirect(url_for('admin.dashboard'))
    
    admin_token = session.get('admin_token')
    return render_template('edit_post.html', title='새 글 작성', form=form, post_id=None, current_user=current_user, admin_token=admin_token)

@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(current_user, post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    form = PostForm(obj=post) # Pre-populate form
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.is_published.data = post.is_published
        form.meta_description.data = post.meta_description
        form.alt_text.data = post.alt_text
        form.video_embed_url.data = post.video_embed_url
        form.tags.data = post.tags # Populate tags field

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.alt_text = form.alt_text.data
        post.video_embed_url = form.video_embed_url.data
        post.meta_description = form.meta_description.data
        post.updated_at = datetime.now(timezone.utc)
        post.tags = form.tags.data # Save tags string directly

        # Determine if publishing or saving as draft
        if 'publish' in request.form:
            if not post.is_published: # If it was a draft and now being published
                post.published_at = datetime.now(timezone.utc)
            post.is_published = True
            flash_message = '글이 성공적으로 발행되었습니다!'
        else: # Default to saving as draft
            if post.is_published: # If it was published and now being saved as draft
                post.published_at = None # Clear published_at if it's now a draft
            post.is_published = False
            flash_message = '글이 임시 저장되었습니다.'

        if form.image.data:
            file = form.image.data
            if _allowed_file(file.filename):
                if post.image_filename:
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.image_filename)
                    if os.path.exists(old_image_path):
                        try: os.remove(old_image_path)
                        except OSError as e: current_app.logger.error(f"Error deleting old image {old_image_path}: {e}")
                
                s_filename = secure_filename(file.filename)
                new_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{s_filename}"
                try:
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename))
                    optimize_image(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)) # Optimize the saved image
                    post.image_filename = new_filename
                except Exception as e:
                    flash(f'이미지 업데이트 중 오류 발생: {e}', 'danger')
                    current_app.logger.error(f"Image update error: {e}")
            elif file.filename != '':
                 flash('허용되지 않는 이미지 파일 형식입니다. 이미지는 업데이트되지 않았습니다.', 'warning')

        db.session.commit()
        flash(flash_message, 'success')
        return redirect(url_for('admin.dashboard'))
    
    current_image_url = url_for('admin.uploaded_file', filename=post.image_filename) if post.image_filename else None
    admin_token = session.get('admin_token')
    return render_template('edit_post.html', title='글 수정', form=form, post_id=post.id, 
                           current_image_url=current_image_url, current_user=current_user, 
                           admin_token=admin_token, post_status=post.is_published)

@bp_admin.route('/post/delete/<int:post_id>', methods=['POST'])
@token_required
def delete_post(current_user, post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if post.image_filename:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.image_filename)
        if os.path.exists(image_path):
            try: os.remove(image_path)
            except OSError as e: current_app.logger.error(f"Error deleting image {image_path}: {e}")

    db.session.delete(post)
    db.session.commit()
    flash('글이 성공적으로 삭제되었습니다.', 'success')
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
@bp_admin.route('/export_content', methods=['GET'])
@token_required
def export_content(current_user):
    try:
        export_data = {
            "meta": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "export_format_version": "1.0"
            },
            "data": {
                "posts": []
            }
        }

        posts = Post.query.order_by(Post.created_at.asc()).all()

        for post_item in posts:
            post_dict = {
                "title": post_item.title,
                "content": post_item.content,
                "created_at": post_item.created_at.isoformat() if post_item.created_at else None,
                "updated_at": post_item.updated_at.isoformat() if post_item.updated_at else None,
                "is_published": post_item.is_published,
                "image_filename": post_item.image_filename,
                "alt_text": post_item.alt_text,
                "meta_description": post_item.meta_description if post_item.meta_description else "", # Handle None meta_description
                "views": post_item.views,
                "author_username": post_item.author.username if post_item.author else None,
                "comments": []
            }

            comments = Comment.query.filter_by(post_id=post_item.id).order_by(Comment.created_at.asc()).all()
            for comment_item in comments:
                post_dict["comments"].append({
                    "nickname": comment_item.nickname,
                    "content": comment_item.content,
                    "created_at": comment_item.created_at.isoformat() if comment_item.created_at else None
                })
            
            export_data["data"]["posts"].append(post_dict)

        export_json = jsonify(export_data).get_data(as_text=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"blog_export_{timestamp}.json"

        return Response(
            export_json,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    except Exception as e:
        current_app.logger.error(f"Error during content export: {e}")
        flash('콘텐츠를 내보내는 중 오류가 발생했습니다.', 'danger')
        return redirect(url_for('admin.dashboard'))

@bp_admin.route('/export/all_content', methods=['GET'])
@admin_required
def export_all_content(current_user):
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
            if post.image_filename:
                source_image_path = os.path.join(current_app.static_folder, 'uploads', post.image_filename)
                if os.path.exists(source_image_path):
                    # Copy image to temp dir
                    shutil.copy(source_image_path, images_temp_dir)
                    relative_image_path = f'images/{post.image_filename}' # Path within the zip
            
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

@bp_admin.route('/import/all_content', methods=['POST'])
@admin_required
def import_all_content(current_user):
    if 'backup_file' not in request.files:
        flash('백업 파일이 없습니다.', 'danger')
        return redirect(url_for('admin.dashboard'))

    file = request.files['backup_file']
    if file.filename == '':
        flash('선택된 파일이 없습니다.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if file and file.filename.endswith('.zip'):
        upload_temp_dir = None # To ensure it's defined for finally block
        try:
            # Save uploaded zip to a temporary file
            temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            file.save(temp_zip_file.name)
            temp_zip_file.close() # Close the file handle so zipfile can open it

            # Create a temporary directory to extract files
            upload_temp_dir = tempfile.mkdtemp()

            # Extract the zip file
            with zipfile.ZipFile(temp_zip_file.name, 'r') as zip_ref:
                zip_ref.extractall(upload_temp_dir)
            
            # Find and read blog_export.json
            json_path = os.path.join(upload_temp_dir, 'blog_export.json')
            if not os.path.exists(json_path):
                flash('백업 파일에 blog_export.json 파일이 없습니다.', 'danger')
                raise FileNotFoundError("blog_export.json not found in backup.")

            with open(json_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # For now, just log or flash success
            current_app.logger.info(f"Successfully read backup data. Posts: {len(backup_data.get('posts', []))}, Comments: {len(backup_data.get('comments', []))}")
            flash('백업 파일을 성공적으로 읽었습니다. 복원 처리를 시작합니다 (현재는 로깅만).', 'success')
            
            original_post_id_to_new_id_map = {}
            if 'posts' in backup_data:
                for post_data in backup_data['posts']:
                    new_image_filename = None
                    if post_data.get('featured_image_url'): # This is a relative path like 'images/filename.jpg'
                        original_image_relative_path = post_data['featured_image_url']
                        # image_filename_only should be 'filename.jpg'
                        image_filename_only = os.path.basename(original_image_relative_path)
                        
                        source_image_path_in_zip = os.path.join(upload_temp_dir, 'images', image_filename_only)
                        
                        if os.path.exists(source_image_path_in_zip):
                            # Ensure unique filename in static/uploads
                            fn, ext = os.path.splitext(image_filename_only)
                            timestamp_suffix = datetime.now().strftime("%Y%m%d%H%M%S%f") # Microseconds for more uniqueness
                            new_image_filename = f"{fn}_{timestamp_suffix}{ext}"
                            destination_image_path = os.path.join(current_app.static_folder, 'uploads', new_image_filename)
                            
                            # Ensure uploads directory exists
                            os.makedirs(os.path.join(current_app.static_folder, 'uploads'), exist_ok=True)
                            shutil.copy(source_image_path_in_zip, destination_image_path)
                        else:
                            current_app.logger.warning(f"Image {image_filename_only} referenced in JSON but not found in backup images folder.")

                    # Convert ISO string dates to datetime objects
                    # Removing 'Z' if present, as fromisoformat might not handle it directly depending on Python version
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
                        image_filename=new_image_filename, # Store the new, unique filename
                        tags=post_data.get('tags'),
                        meta_description=post_data.get('meta_description'),
                        slug=post_data.get('slug'), # Consider slug uniqueness later if needed
                        user_id=current_user.id # Assign to current admin user
                        # Views will default to 0
                    )
                    db.session.add(new_post)
                    db.session.flush() # Flush to get the new_post.id for mapping
                    if post_data.get('id'): # Original ID from backup
                        original_post_id_to_new_id_map[str(post_data['id'])] = new_post.id
            
            # 2. Restore Comments (mapping IDs)
            original_comment_id_to_new_id_map = {}
            comments_to_update_parent_id = [] # Stores tuples of (comment_object, original_parent_id_str)

            if 'comments' in backup_data:
                for comment_data in backup_data['comments']:
                    original_post_id_str = str(comment_data.get('post_original_id'))
                    new_post_id = original_post_id_to_new_id_map.get(original_post_id_str)

                    if not new_post_id:
                        current_app.logger.warning(f"Comment (original ID: {comment_data.get('id')}) references non-existent or unmapped post (original ID: {original_post_id_str}). Skipping.")
                        continue

                    created_at_dt = datetime.fromisoformat(comment_data['created_at'].replace('Z', '')) if comment_data.get('created_at') else datetime.utcnow()
                    
                    new_comment = Comment(
                        nickname=comment_data.get('nickname'),
                        content=comment_data.get('content'),
                        created_at=created_at_dt,
                        post_id=new_post_id
                        # ip_address is intentionally not restored for privacy.
                        # parent_id will be set in a second pass if applicable.
                    )
                    db.session.add(new_comment)
                    db.session.flush() # Flush to get the new_comment.id for mapping

                    original_comment_id_str = str(comment_data.get('id'))
                    if original_comment_id_str:
                        original_comment_id_to_new_id_map[original_comment_id_str] = new_comment.id
                    
                    original_parent_id_str = str(comment_data.get('parent_original_id'))
                    if original_parent_id_str and original_parent_id_str != 'None': # Ensure it's a valid ID string
                        comments_to_update_parent_id.append({'comment_obj': new_comment, 'original_parent_id': original_parent_id_str})
            
                # Second pass to update parent_id for comments
                for item in comments_to_update_parent_id:
                    comment_to_update = item['comment_obj']
                    original_parent_id_str = item['original_parent_id']
                    new_parent_id = original_comment_id_to_new_id_map.get(original_parent_id_str)
                    if new_parent_id:
                        comment_to_update.parent_id = new_parent_id
                    else:
                        current_app.logger.warning(f"Could not find new parent ID for comment (new ID: {comment_to_update.id}) with original parent ID {original_parent_id_str}. Parent comment might not have been in the backup or failed to import.")
            
            db.session.commit() # Commit after all posts and comments are processed

            flash('콘텐츠 복원이 완료되었습니다 (게시물 및 댓글).', 'success')
            current_app.logger.info(f"Post ID map: {original_post_id_to_new_id_map}")
            current_app.logger.info(f"Comment ID map: {original_comment_id_to_new_id_map}")

            return redirect(url_for('admin.dashboard'))

        except FileNotFoundError as fnf_error:
            current_app.logger.error(f"Import error: {fnf_error}")
            # flash message already set
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            current_app.logger.error(f"Error importing content from ZIP: {e}")
            flash(f'콘텐츠를 ZIP에서 가져오는 중 오류가 발생했습니다: {e}', 'danger')
            return redirect(url_for('admin.dashboard'))
        finally:
            # Clean up temporary uploaded zip file
            if 'temp_zip_file' in locals() and os.path.exists(temp_zip_file.name):
                os.remove(temp_zip_file.name)
            # Clean up temporary extraction directory
            if upload_temp_dir and os.path.exists(upload_temp_dir):
                shutil.rmtree(upload_temp_dir)
    else:
        flash('잘못된 파일 형식입니다. ZIP 파일을 업로드해주세요.', 'danger')
        return redirect(url_for('admin.dashboard'))

@bp_admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings(current_user_from_token):
    form = SettingsForm(obj=current_user_from_token)
    if form.validate_on_submit():
        form.populate_obj(current_user_from_token)
        db.session.commit()
        flash('관리자 설정이 성공적으로 저장되었습니다.', 'success')
    return render_template('admin_settings.html', title='관리자 설정', form=form, current_user=current_user_from_token)
