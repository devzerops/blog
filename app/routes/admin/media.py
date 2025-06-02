"""
Admin media management routes.
Contains routes for uploading and managing media files.
"""

import os
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory, render_template, url_for, flash

from app import file_util
from app.auth import admin_required, token_required
from app.routes.admin import bp_admin
from app.models import Post


@bp_admin.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """Handle file uploads"""
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'No file part in the request'}}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # 파일 업로드 처리
        file_info = file_util.save_uploaded_file(file, subfolder='')
        
        # 성공 응답 반환
        return jsonify({
            'url': url_for('public.uploaded_file', filename=file_info['saved_name']),
            'filename': file_info['saved_name'],
            'original_name': file_info['original_name']
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp_admin.route('/upload_editor_image', methods=['POST'])
@token_required
def upload_editor_image(current_user):
    """Handle image uploads from the editor"""
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'No file part in the request'}}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # 에디터용 이미지 업로드 (원본 크기 유지)
        file_info = file_util.save_uploaded_file(file, subfolder='')
        
        # CKEditor 형식으로 응답 반환
        image_url = url_for('static', filename=f'uploads/{file_info["saved_name"]}', _external=True)
        return jsonify({'location': image_url})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp_admin.route('/uploads/<path:filename>')
@token_required
def uploaded_file(current_user, filename):
    """Serve uploaded files"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp_admin.route('/delete-image', methods=['POST'])
@admin_required
def delete_image(current_user):
    """Delete an uploaded image"""
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'error': 'Filename is required'}), 400
    
    try:
        # 파일 삭제 시 서브폴더 정보도 함께 전달
        file_util.delete_uploaded_file(data['filename'], subfolder='')
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error deleting image: {str(e)}')
        return jsonify({'error': str(e)}), 500


@bp_admin.route('/image-management', methods=['GET'])
@admin_required
def image_management(current_user):
    """Image management interface"""
    # Get all posts with their cover images
    posts = Post.query.all()
    posts_data = []
    
    for post in posts:
        post_data = {
            'id': post.id,
            'title': post.title,
            'cover_image_url': url_for('static', filename=f'uploads/thumbnails/{post.thumbnail_filename}') if post.thumbnail_filename else None,
            'alt_text': post.alt_text,
            'inline_image_urls': []
        }
        
        # Extract image URLs from post content (if any)
        import re
        img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', post.content or '')
        post_data['inline_image_urls'] = img_tags
        
        posts_data.append(post_data)
    
    # Get list of all uploaded images for reference
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
    all_images = []
    
    if os.path.exists(upload_dir):
        for root, _, files in os.walk(upload_dir):
            for filename in files:
                if file_util.allowed_file(filename):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
                    stat = os.stat(file_path)
                    
                    all_images.append({
                        'name': filename,
                        'path': rel_path,
                        'url': url_for('static', filename=f'uploads/{rel_path}'),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    # Sort images by modification time (newest first)
    all_images.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('admin/admin_image_management.html', 
                          title='이미지 관리',
                          posts_data=posts_data,
                          all_images=all_images,
                          current_user=current_user)
