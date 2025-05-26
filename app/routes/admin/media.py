"""
Admin media management routes.
Contains routes for uploading and managing media files.
"""

import os
import json
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

from app.auth import admin_required, token_required
from app.routes.admin import bp_admin


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp_admin.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """Handle file uploads"""
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'No file part in the request'}}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwriting
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Return success response with file info
        return jsonify({
            'url': url_for('public.uploaded_file', filename=unique_filename),
            'filename': unique_filename,
            'original_name': original_filename
        }), 200
    
    return jsonify({'error': 'File type not allowed'}), 400


@bp_admin.route('/upload_editor_image', methods=['POST'])
@token_required
def upload_editor_image(current_user):
    """Handle image uploads from the editor"""
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'No file part in the request'}}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwriting
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Return success response in CKEditor format
        image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
        return jsonify({'location': image_url})
    
    return jsonify({'error': 'File type not allowed'}), 400


@bp_admin.route('/uploads/<path:filename>')
@token_required
def uploaded_file(current_user, filename):
    """Serve uploaded files"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp_admin.route('/image-management', methods=['GET'])
@admin_required
def image_management(current_user):
    """Image management interface"""
    # Get list of uploaded images
    upload_dir = current_app.config['UPLOAD_FOLDER']
    images = []
    
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            if allowed_file(filename):
                file_path = os.path.join(upload_dir, filename)
                stat = os.stat(file_path)
                images.append({
                    'name': filename,
                    'url': url_for('public.uploaded_file', filename=filename),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # Sort images by modification time (newest first)
    images.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('admin/admin_image_management.html', 
                          title='이미지 관리', 
                          images=images, 
                          current_user=current_user)
