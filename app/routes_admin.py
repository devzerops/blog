from flask import (
    Blueprint, render_template, redirect, url_for, 
    request, flash, current_app, send_from_directory, jsonify
)
from app.auth import token_required
from app.models import Post # User model not directly used here, but through current_user from token_required
from app.database import db
from werkzeug.utils import secure_filename
import os
# import markdown # Not needed for admin routes directly, but for public display
from datetime import datetime, timezone
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL as URLValidator # Renamed to avoid conflict
from flask_wtf.file import FileAllowed

bp_admin = Blueprint('admin', __name__)

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=1, max=140)])
    content = TextAreaField('내용 (Markdown 지원)') 
    image = FileField('커버 이미지 (선택)', validators=[
        Optional(), 
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '이미지 파일(jpg, jpeg, png, gif)만 업로드 가능합니다!')
    ])
    video_embed_url = URLField('동영상 URL (선택, 예: YouTube)', validators=[Optional(), URLValidator()])
    tags = StringField('태그 (쉼표로 구분, 선택)', validators=[Optional(), Length(max=200)])
    submit = SubmitField('저장') # Changed from '발행' for consistency

def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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
                # Secure filename and make it unique
                s_filename = secure_filename(file.filename)
                filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{s_filename}"
                try:
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    flash(f'이미지 저장 중 오류 발생: {e}', 'danger')
                    current_app.logger.error(f"Image save error: {e}")
                    filename = None # Ensure filename is None if save fails
            else:
                flash('허용되지 않는 이미지 파일 형식입니다.', 'warning')
                # Do not proceed with post creation if image was mandatory and failed, or handle as needed

        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            image_filename=filename,
            video_embed_url=form.video_embed_url.data,
            tags=form.tags.data.strip()
        )
        db.session.add(post)
        db.session.commit()
        flash('새로운 글이 성공적으로 작성되었습니다!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('edit_post.html', title='새 글 작성', form=form, post_id=None, current_user=current_user)

@bp_admin.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(current_user, post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    form = PostForm(obj=post) # Pre-populate form

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.video_embed_url = form.video_embed_url.data
        post.tags = form.tags.data.strip()
        post.updated_at = datetime.now(timezone.utc)

        if form.image.data:
            file = form.image.data
            if _allowed_file(file.filename):
                # Delete old image if it exists
                if post.image_filename:
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.image_filename)
                    if os.path.exists(old_image_path):
                        try: os.remove(old_image_path)
                        except OSError as e: current_app.logger.error(f"Error deleting old image {old_image_path}: {e}")
                
                s_filename = secure_filename(file.filename)
                new_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{s_filename}"
                try:
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename))
                    post.image_filename = new_filename
                except Exception as e:
                    flash(f'이미지 업데이트 중 오류 발생: {e}', 'danger')
                    current_app.logger.error(f"Image update error: {e}")
            elif file.filename != '': # File was provided but not allowed
                 flash('허용되지 않는 이미지 파일 형식입니다. 이미지는 업데이트되지 않았습니다.', 'warning')

        db.session.commit()
        flash('글이 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    current_image_url = url_for('admin.uploaded_file', filename=post.image_filename) if post.image_filename else None
    return render_template('edit_post.html', title='글 수정', form=form, post_id=post.id, current_image_url=current_image_url, current_user=current_user)

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
            # The URL returned should be accessible by the editor to display the image.
            # If UPLOAD_FOLDER is under static, url_for can generate it.
            # If it's outside static, you'll need a dedicated route like uploaded_file.
            # Assuming UPLOAD_FOLDER is 'app/static/uploads' as per original plan.
            # The 'admin.uploaded_file' route needs to be accessible without token if images are public.
            # For now, let's assume it's okay for admin to see it via this route.
            image_url = url_for('admin.uploaded_file', filename=unique_filename, _external=True)
            return jsonify({'location': image_url})
        except Exception as e:
            current_app.logger.error(f"Editor image upload error: {e}")
            return jsonify({'error': {'message': f'Image upload failed: {e}'}}), 500
    else:
        return jsonify({'error': {'message': 'File type not allowed'}}), 400
