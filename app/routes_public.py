from flask import Blueprint, render_template, request, current_app, abort, url_for, session, send_from_directory, redirect, flash
from markupsafe import Markup # Import Markup from markupsafe
from app.models import Post, Tag, db, User, Comment # Added User, Comment
from app.forms import CommentForm # Import CommentForm
from app.database import db # Import db
import os # Added: Import the 'os' module
import re  # For regex operations to remove image tags

bp_public = Blueprint('public', __name__)

@bp_public.route('/robots.txt')
def robots_txt():
    current_app.logger.info(f"Attempting to serve robots.txt from: {current_app.static_folder}")
    try:
        response = send_from_directory(current_app.static_folder, 'robots.txt')
        current_app.logger.info(f"robots.txt found and sending response: {response.status_code}")
        return response
    except Exception as e:
        current_app.logger.error(f"Error serving robots.txt: {e}")
        abort(404)

@bp_public.route('/')
@bp_public.route('/posts')
def post_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', None)
    
    query_obj = Post.query.filter(Post.is_published == True) # Show only published posts

    if search_query:
        search_term = f"%{search_query}%"
        query_obj = query_obj.filter(
            db.or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term)
            )
        )
        title = f'"{search_query}" 검색 결과'
    else:
        title = '블로그 게시글'

    posts_pagination = query_obj.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 10), error_out=False
    )
    posts_items = posts_pagination.items
    
    # Prepare posts for display (e.g., generate image URLs)
    processed_posts = []
    for post_item in posts_items:
        image_url = None
        if post_item.image_filename:
            if 'static/uploads' in current_app.config['UPLOAD_FOLDER']:
                 # app/static/uploads -> static/uploads/filename
                relative_upload_path = os.path.join('uploads', post_item.image_filename)
                image_url = url_for('static', filename=relative_upload_path) 
            else:
                # If UPLOAD_FOLDER is not directly under static, this needs a dedicated public serving route.
                # For simplicity, we will assume UPLOAD_FOLDER is 'app/static/uploads'
                # This was set in config.py as os.path.join(basedir, 'app', 'static', 'uploads')
                image_url = url_for('static', filename=f'uploads/{post_item.image_filename}')

        processed_posts.append({
            'id': post_item.id,
            'title': post_item.title,
            'created_at': post_item.created_at,
            'author_username': post_item.author.username, # Assuming author relationship is eager loaded or accessible
            'tags': post_item.tags, # Pass raw string, template will split
            'image_url': image_url,
            'alt_text': post_item.alt_text if post_item.alt_text else post_item.title, # Add alt_text, fallback to title
            'summary': Markup(post_item.content), # Display full HTML content for now
            'views': post_item.views # Add views count
        })
        
    return render_template('post_list.html', title=title, posts=processed_posts, pagination=posts_pagination, search_query=search_query)

@bp_public.route('/posts/<int:post_id>')
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, is_published=True).first_or_404()

    # View counting logic
    viewed_posts_session_key = f'viewed_post_{post.id}'
    if viewed_posts_session_key not in session:
        post.views += 1
        session[viewed_posts_session_key] = True
        db.session.commit()

    html_content = Markup(post.content) # Content is now HTML from TinyMCE
    
    # Prepare meta description (simple truncation, consider HTML stripping for production)
    # For TinyMCE content, which is HTML, we need a proper way to get text.
    # For now, let's assume post.content is the raw HTML and we'll strip it crudely or use a summary if available.
    # A better approach would be to store a plain text summary or use a library to convert HTML to text.
    plain_content_for_meta = Markup(post.content).striptags() # Basic stripping
    meta_description = (plain_content_for_meta[:155] + '...') if len(plain_content_for_meta) > 155 else plain_content_for_meta

    image_url = None
    if post.image_filename:
        if 'static/uploads' in current_app.config['UPLOAD_FOLDER']:
            image_url = url_for('static', filename=f'uploads/{post.image_filename}')
        # else: handle non-static UPLOAD_FOLDER serving if necessary

    # Comment form and comments list
    form = CommentForm()
    comments = post.comments.order_by(Comment.created_at.asc()).all()

    return render_template('post_detail.html', 
                           title=post.title, 
                           post=post, 
                           html_content=html_content, 
                           image_url=image_url,
                           meta_description=meta_description, # Pass meta_description
                           comment_form=form, # Pass comment form
                           comments=comments) # Pass comments list

@bp_public.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            nickname=form.nickname.data,
            content=form.content.data,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('댓글이 성공적으로 등록되었습니다.', 'success')
    else:
        # Store errors in flash to display on the post_detail page after redirect
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('public.post_detail', post_id=post.id))

@bp_public.route('/tags/<string:tag_name>')
def posts_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    
    # Find the tag object (case-insensitive)
    tag = Tag.query.filter(db.func.lower(Tag.name) == db.func.lower(tag_name)).first()

    if tag:
        posts_pagination = Post.query.join(Post.tags).filter(Tag.id == tag.id, Post.is_published == True)\
                                     .order_by(Post.created_at.desc())\
                                     .paginate(page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 10), error_out=False)
    else:
        # If tag doesn't exist, return an empty pagination object or handle as preferred
        from flask_sqlalchemy.pagination import Pagination
        posts_pagination = Pagination(None, page, current_app.config.get('POSTS_PER_PAGE', 10), 0, [])

    posts_items = posts_pagination.items

    processed_posts = []
    for post_item in posts_items:
        image_url = None
        if post_item.image_filename:
            if 'static/uploads' in current_app.config['UPLOAD_FOLDER']:
                image_url = url_for('static', filename=f'uploads/{post_item.image_filename}')
        processed_posts.append({
            'id': post_item.id,
            'title': post_item.title,
            'created_at': post_item.created_at,
            'author_username': post_item.author.username,
            'tags': post_item.tags, # This is now a list of Tag objects
            'image_url': image_url,
            'alt_text': post_item.alt_text if post_item.alt_text else post_item.title, 
            'summary': Markup(post_item.content), 
            'views': post_item.views
        })

    return render_template('post_list.html', 
                           title=f'"{tag_name}" 태그가 포함된 글', 
                           posts=processed_posts, 
                           pagination=posts_pagination, 
                           tag_filter=tag_name)

@bp_public.route('/about')
def about_page():
    return render_template('about.html', title='About Us')
