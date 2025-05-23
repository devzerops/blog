from flask import Blueprint, render_template, request, current_app, abort, url_for
from app.models import Post
import markdown
from markupsafe import Markup # For rendering HTML content safely
import os # Added: Import the 'os' module

bp_public = Blueprint('public', __name__)

@bp_public.route('/')
@bp_public.route('/posts')
def post_list():
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
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
            'summary': Markup(markdown.markdown(post_item.content[:200] + ('...' if len(post_item.content) > 200 else ''), 
                                             extensions=['fenced_code', 'tables', 'nl2br']))
        })
        
    return render_template('post_list.html', title='블로그 게시글', posts=processed_posts, pagination=posts_pagination)

@bp_public.route('/posts/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    html_content = Markup(markdown.markdown(post.content, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']))
    
    image_url = None
    if post.image_filename:
        if 'static/uploads' in current_app.config['UPLOAD_FOLDER']:
            image_url = url_for('static', filename=f'uploads/{post.image_filename}')
        # else: handle non-static UPLOAD_FOLDER serving if necessary

    # Prepare tags
    tags_list = post.tags.split(',') if post.tags else []

    return render_template('post_detail.html', 
                           title=post.title, 
                           post=post, 
                           html_content=html_content, 
                           image_url=image_url,
                           tags_list=tags_list)

@bp_public.route('/tags/<string:tag_name>')
def posts_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    # Case-insensitive search for tags
    posts_pagination = Post.query.filter(Post.tags.ilike(f'%{tag_name}%'))\
                                 .order_by(Post.created_at.desc())\
                                 .paginate(page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 10), error_out=False)
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
            'tags': post_item.tags, # Pass raw string, template will split
            'image_url': image_url,
            'summary': Markup(markdown.markdown(post_item.content[:200] + ('...' if len(post_item.content) > 200 else ''), 
                                             extensions=['fenced_code', 'tables', 'nl2br']))
        })

    return render_template('post_list.html', 
                           title=f'"{tag_name}" 태그가 포함된 글', 
                           posts=processed_posts, 
                           pagination=posts_pagination, 
                           tag_filter=tag_name)
