"""
Admin backup and restore routes.
Contains routes for backing up and restoring site data.
"""

import os
import json
import csv
import datetime
import tempfile
import shutil
import zipfile
from io import StringIO
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from app.database import db
from app.models import Post, Category, Comment, User, PageView, SiteSetting
from app.forms import ImportForm
from app.auth import admin_required
from app.routes.admin import bp_admin


@bp_admin.route('/export/all_content', methods=['GET'])
@admin_required
def export_all_content(current_user):
    """Export all site content as ZIP including JSON data and images"""
    try:
        # 1. Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        images_temp_dir = os.path.join(temp_dir, 'images')
        os.makedirs(images_temp_dir, exist_ok=True)
        
        # 2. Prepare the data
        # Export posts with images
        posts_data = []
        posts = Post.query.order_by(Post.created_at.asc()).all()
        for post in posts:
            relative_image_path = None
            if post.image_filename:  # 이미지 필드가 있는 경우
                image_filename_only = post.image_filename  # 파일명만 사용
                source_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename_only)
                if os.path.exists(source_image_path):
                    # Copy image to temp dir
                    shutil.copy(source_image_path, images_temp_dir)
                    relative_image_path = f'images/{image_filename_only}'  # Path within the zip
            
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.isoformat() + 'Z' if post.created_at else None,
                'updated_at': post.updated_at.isoformat() + 'Z' if post.updated_at else None,
                'is_published': post.is_published,
                'published_at': post.published_at.isoformat() + 'Z' if post.published_at else None,
                'user_id': post.user_id,
                'category_id': post.category_id,
                'tags': post.tags, 
                'slug': post.slug,
                'featured_image_url': relative_image_path  # Include relative path to image in ZIP
            }
            posts_data.append(post_data)
        
        # Export categories
        categories_data = []
        categories = Category.query.all()
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name
            }
            categories_data.append(category_data)
        
        # Export comments
        comments_data = []
        comments = Comment.query.order_by(Comment.created_at.asc()).all()
        for comment in comments:
            comment_data = {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
                'post_id': comment.post_id,
                'parent_id': comment.parent_id,
                'nickname': comment.nickname,
                'ip_address': str(comment.ip_address) if comment.ip_address else None
            }
            comments_data.append(comment_data)
        
        # Export site settings
        site_settings_data = None
        site_settings = SiteSetting.query.first()
        if site_settings:
            site_settings_data = {
                'site_title': site_settings.site_title,
                'site_description': site_settings.site_description,
                'footer_copyright_text': site_settings.footer_copyright_text,
                'google_analytics_id': site_settings.google_analytics_id,
                'about_content': site_settings.about_content
            }
        
        # 3. Combine all data
        export_data = {
            'posts': posts_data,
            'categories': categories_data,
            'comments': comments_data,
            'site_settings': site_settings_data
        }
        
        # 4. Save JSON to temp dir
        json_filename = 'blog_export.json'
        json_temp_path = os.path.join(temp_dir, json_filename)
        with open(json_temp_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)
        
        # 5. Create ZIP archive
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'blog_export_{timestamp}.zip'
        zip_temp_path = os.path.join(tempfile.gettempdir(), zip_filename)  # Store zip in system temp
        
        with zipfile.ZipFile(zip_temp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add JSON file to zip
            zf.write(json_temp_path, arcname=json_filename)
            # Add images to zip
            for root, _, files in os.walk(images_temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('images', file)  # Store images in 'images/' folder in zip
                    zf.write(file_path, arcname=arcname)
        
        # 6. Send the ZIP file as download
        return send_file(zip_temp_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        current_app.logger.error(f"Error exporting content as ZIP: {e}")
        flash('콘텐츠를 ZIP으로 내보내는 중 오류가 발생했습니다.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    finally:
        # 7. Clean up temp directories
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@bp_admin.route('/data/restore', methods=['GET', 'POST'])
@admin_required
def data_restore(current_user):
    """Restore site data from backup"""
    form = ImportForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        file = form.backup_file.data
        if file and file.filename.endswith('.zip'):
            # Create a temporary directory to extract the ZIP
            temp_dir = tempfile.mkdtemp()
            try:
                # Save the uploaded ZIP file
                zip_path = os.path.join(temp_dir, secure_filename(file.filename))
                file.save(zip_path)
                
                # Extract the ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Look for the JSON data file
                json_path = os.path.join(temp_dir, 'blog_export.json')
                if not os.path.exists(json_path):
                    flash('백업 파일에서 데이터 파일(blog_export.json)을 찾을 수 없습니다.', 'danger')
                    return redirect(url_for('admin.data_restore'))
                
                # Read and parse JSON data
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.loads(f.read())
                
                # Begin transaction
                db.session.begin_nested()
                
                # Restore categories
                for category_data in data.get('categories', []):
                    # Check if category exists
                    category = Category.query.filter_by(id=category_data.get('id')).first()
                    if category:
                        # Update existing category
                        category.name = category_data.get('name')
                    else:
                        # Create new category
                        category = Category(
                            id=category_data.get('id'),
                            name=category_data.get('name')
                        )
                        db.session.add(category)
                
                # Restore posts
                for post_data in data.get('posts', []):
                    # Check if post exists
                    post = Post.query.filter_by(id=post_data.get('id')).first()
                    
                    # Parse dates (strip 'Z' suffix if present)
                    created_at = None
                    if post_data.get('created_at'):
                        created_at_str = post_data.get('created_at')
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str[:-1]  # Remove 'Z' suffix
                        created_at = datetime.fromisoformat(created_at_str)
                        
                    updated_at = None
                    if post_data.get('updated_at'):
                        updated_at_str = post_data.get('updated_at')
                        if updated_at_str.endswith('Z'):
                            updated_at_str = updated_at_str[:-1]  # Remove 'Z' suffix
                        updated_at = datetime.fromisoformat(updated_at_str)
                        
                    published_at = None
                    if post_data.get('published_at'):
                        published_at_str = post_data.get('published_at')
                        if published_at_str.endswith('Z'):
                            published_at_str = published_at_str[:-1]  # Remove 'Z' suffix
                        published_at = datetime.fromisoformat(published_at_str)
                    
                    # Handle image restoration
                    image_filename = None
                    featured_image_url = post_data.get('featured_image_url')
                    if featured_image_url and featured_image_url.startswith('images/'):
                        image_name = os.path.basename(featured_image_url)
                        zip_image_path = os.path.join(temp_dir, featured_image_url)
                        if os.path.exists(zip_image_path):
                            # Ensure upload directory exists
                            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                            
                            # Copy image to uploads folder
                            target_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_name)
                            shutil.copy(zip_image_path, target_path)
                            image_filename = image_name
                    
                    if post:
                        # Update existing post
                        post.title = post_data.get('title')
                        post.content = post_data.get('content')
                        post.created_at = created_at
                        post.updated_at = updated_at
                        post.is_published = post_data.get('is_published')
                        post.published_at = published_at
                        post.user_id = post_data.get('user_id')  # Note: using user_id not author_id
                        post.category_id = post_data.get('category_id')
                        post.tags = post_data.get('tags')
                        post.slug = post_data.get('slug')
                        if image_filename:
                            post.image_filename = image_filename
                    else:
                        # Create new post
                        post = Post(
                            id=post_data.get('id'),
                            title=post_data.get('title'),
                            content=post_data.get('content'),
                            created_at=created_at,
                            updated_at=updated_at,
                            is_published=post_data.get('is_published'),
                            published_at=published_at,
                            user_id=post_data.get('user_id'),  # Note: using user_id not author_id
                            category_id=post_data.get('category_id'),
                            tags=post_data.get('tags'),
                            slug=post_data.get('slug'),
                            image_filename=image_filename
                        )
                        db.session.add(post)
                
                # Restore comments
                for comment_data in data.get('comments', []):
                    # Check if comment exists
                    comment = Comment.query.filter_by(id=comment_data.get('id')).first()
                    
                    # Parse dates (strip 'Z' suffix if present)
                    created_at = None
                    if comment_data.get('created_at'):
                        created_at_str = comment_data.get('created_at')
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str[:-1]  # Remove 'Z' suffix
                        created_at = datetime.fromisoformat(created_at_str)
                    
                    if comment:
                        # Update existing comment
                        comment.nickname = comment_data.get('nickname')
                        comment.content = comment_data.get('content')
                        comment.created_at = created_at
                        comment.post_id = comment_data.get('post_id')
                        comment.parent_id = comment_data.get('parent_id')
                        if comment_data.get('ip_address'):
                            comment.ip_address = comment_data.get('ip_address')
                    else:
                        # Create new comment
                        comment = Comment(
                            id=comment_data.get('id'),
                            nickname=comment_data.get('nickname'),
                            content=comment_data.get('content'),
                            created_at=created_at,
                            post_id=comment_data.get('post_id'),
                            parent_id=comment_data.get('parent_id'),
                            ip_address=comment_data.get('ip_address')
                        )
                        db.session.add(comment)
                
                # Restore site settings
                site_settings_data = data.get('site_settings')
                if site_settings_data:
                    # Get or create site settings
                    site_settings = SiteSetting.query.first()
                    if not site_settings:
                        site_settings = SiteSetting()
                        db.session.add(site_settings)
                    
                    # Update site settings
                    site_settings.site_title = site_settings_data.get('site_title')
                    site_settings.site_description = site_settings_data.get('site_description')
                    site_settings.footer_copyright_text = site_settings_data.get('footer_copyright_text')
                    site_settings.google_analytics_id = site_settings_data.get('google_analytics_id')
                    site_settings.about_content = site_settings_data.get('about_content')
                
                # Commit all changes
                db.session.commit()
                
                flash('데이터와 이미지를 포함한 모든 콘텐츠가 성공적으로 복원되었습니다.', 'success')
                return redirect(url_for('admin.dashboard'))
            
            except Exception as e:
                # Rollback transaction on error
                db.session.rollback()
                current_app.logger.error(f"Error restoring data: {e}")
                flash(f'콘텐츠 복원 중 오류가 발생했습니다: {str(e)}', 'danger')
                return redirect(url_for('admin.data_restore'))
            
            finally:
                # Clean up temporary directory
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        else:
            flash('올바른 ZIP 파일을 업로드해주세요.', 'warning')
    
    return render_template('admin/admin_data_restore.html', title='데이터 복원', import_form=form)
