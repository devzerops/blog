from flask import Blueprint, render_template, request, current_app, abort, url_for, session, send_from_directory, redirect, flash
from markupsafe import Markup # Import Markup from markupsafe
from app.models import Post, db, User, Comment, SiteSetting, Category # Removed Tag, Added User, Comment, SiteSetting, Category
from app.forms import CommentForm # Import CommentForm
from app.database import db # Import db
from app.auth import get_current_user_if_logged_in # Add this import
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
    tag_name = request.args.get('tag', None)
    category_id_filter = request.args.get('category_id', None, type=int) # New: using ID
    selected_category_object = None
    
    # Eager load category relationship
    query_obj = Post.query.options(db.joinedload(Post.category)).filter(Post.is_published == True) # Show only published posts

    title = '블로그 게시글' # Default title

    if tag_name:
        query_obj = query_obj.filter(Post.tags.ilike(f"%{tag_name}%"))
        title = f'"{tag_name}" 태그 글 목록'
    
    if category_id_filter is not None:
        selected_category_object = Category.query.get(category_id_filter)
        if selected_category_object:
            query_obj = query_obj.filter(Post.category_id == category_id_filter)
            category_title_part = f'"{selected_category_object.name}" 카테고리 글 목록'
            if tag_name:
                title = f'"{tag_name}" 태그 및 {category_title_part}'
            else:
                title = category_title_part
        # else: category_id is invalid, silently ignore or flash a message

    if search_query:
        search_term = f"%{search_query}%"
        query_obj = query_obj.filter(
            db.or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term)
            )
        )
        # Adjust title if search is also active
        if tag_name or category_id_filter:
            title += f' 중 "{search_query}" 검색 결과'
        else:
            title = f'"{search_query}" 검색 결과'
    
    # Fetch all unique tags from published posts for the sidebar
    all_published_posts_for_tags = Post.query.filter(Post.is_published == True).all()
    unique_tags = set()
    for post_item_for_tags in all_published_posts_for_tags:
        if post_item_for_tags.tags:
            tags_list = [t.strip() for t in post_item_for_tags.tags.split(',') if t.strip()]
            unique_tags.update(tags_list)
    sorted_unique_tags = sorted(list(unique_tags))

    # Fetch all categories for the sidebar
    all_categories = Category.query.order_by(Category.name).all()

    # Get posts_per_page from SiteSetting or config
    site_settings = SiteSetting.query.first()
    posts_per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    if site_settings and site_settings.posts_per_page:
        posts_per_page = site_settings.posts_per_page

    posts_pagination = query_obj.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=posts_per_page, error_out=False
    )
    posts_items = posts_pagination.items
    
    # Prepare posts for display (e.g., generate image URLs)
    processed_posts = []
    for post_item in posts_items:
        image_url = None
        if post_item.image_filename:
            # Check if UPLOAD_FOLDER is an absolute path or relative to static
            if os.path.isabs(current_app.config['UPLOAD_FOLDER']) and 'static' in current_app.config['UPLOAD_FOLDER']:
                 # Construct URL relative to static folder if UPLOAD_FOLDER is like /app/static/uploads
                static_folder_name = os.path.basename(os.path.normpath(current_app.config['UPLOAD_FOLDER'])) #e.g. 'uploads'
                image_url = url_for('static', filename=f'{static_folder_name}/{post_item.image_filename}')
            else:
                # Fallback or direct URL if not conventionally in static/uploads or using a different setup
                image_url = url_for('public.uploaded_file', filename=post_item.image_filename)

        # Explicitly process category info to avoid object reference issues
        category_info = None
        if post_item.category:
            category_info = {
                'id': post_item.category.id,
                'name': post_item.category.name
            }
            
        processed_posts.append({
            'id': post_item.id,
            'title': post_item.title,
            'created_at': post_item.created_at,
            'author_username': post_item.author.username,
            'tags': post_item.tags,  # Pass the tags string directly
            'image_url': image_url,
            'alt_text': post_item.alt_text if post_item.alt_text else post_item.title, 
            'summary': Markup(post_item.content).striptags()[:200] + ('...' if len(Markup(post_item.content).striptags()) > 200 else ''),
            'views': post_item.views,  
            'comment_count': post_item.comments.count(),
            'category': category_info  # Add the explicit category dictionary
        })
        
    return render_template('post_list.html', 
                           title=title, 
                           posts=processed_posts, 
                           pagination=posts_pagination, 
                           search_query=search_query, 
                           tag_filter=tag_name, 
                           selected_category_id=category_id_filter, # Pass selected category ID
                           all_tags=sorted_unique_tags,
                           all_categories=all_categories) # Pass all_categories

@bp_public.route('/posts/<int:post_id>')
def post_detail(post_id):
    current_user = get_current_user_if_logged_in() # Use the new function

    # Query post by ID only
    post = Post.query.get_or_404(post_id)

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
    form = CommentForm() # For submitting new top-level comments
    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    # 태그 및 카테고리 데이터 가져오기 (왼쪽 내비게이션 바용)
    # 1. 모든 태그 가져오기
    all_posts = Post.query.filter_by(is_published=True).all()
    all_tags_flat = []
    for p in all_posts:
        if p.tags:  # tags가 None이 아닌 경우에만 처리
            tags_list = [tag.strip() for tag in p.tags.split(',') if tag.strip()]
            all_tags_flat.extend(tags_list)
    
    # 중복 제거하고 정렬
    sorted_unique_tags = sorted(set(all_tags_flat))
    
    # 2. 모든 카테고리 가져오기
    all_categories = Category.query.order_by(Category.name).all()
    
    # 이전글과 다음글 가져오기
    # 작성일 기준으로 정렬하여 이전글과 다음글 찾기
    prev_post = Post.query.filter(Post.created_at < post.created_at, Post.is_published == True).order_by(Post.created_at.desc()).first()
    next_post = Post.query.filter(Post.created_at > post.created_at, Post.is_published == True).order_by(Post.created_at.asc()).first()

    return render_template('post_detail.html', 
                           title=post.title, 
                           post=post, 
                           html_content=html_content, 
                           image_url=image_url,
                           meta_description=meta_description, # Pass meta_description
                           comment_form=form, # Pass comment form
                           comments=comments, # Pass comments list
                           current_user=current_user,
                           # 이전글과 다음글 변수
                           prev_post=prev_post,
                           next_post=next_post,
                           # 왼쪽 내비게이션 바를 위한 변수들
                           all_tags=sorted_unique_tags,
                           all_categories=all_categories,
                           tag_filter=None,
                           selected_category_id=None)

@bp_public.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        parent_id = request.form.get('parent_id') # Get parent_id from form data
        parent_id = int(parent_id) if parent_id else None # Convert to int or None

        comment = Comment(
            nickname=form.nickname.data,
            content=form.content.data,
            post_id=post.id,
            ip_address=request.remote_addr, # Store full IP address
            parent_id=parent_id # Set parent_id
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

@bp_public.route('/about')
def about_page():
    current_user = get_current_user_if_logged_in() # Use the new function
    # Get site settings for about content
    site_settings = SiteSetting.query.first()
    about_content = site_settings.about_content if site_settings and site_settings.about_content else None
    return render_template('about.html', title='소개', current_user=current_user, about_content=about_content)

@bp_public.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
