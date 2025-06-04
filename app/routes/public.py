
from flask import Blueprint, render_template, request, abort, jsonify, redirect, url_for
from app.models import Post, Category, Comment, SiteSetting, PageView
from app.database import db
from app.forms import CommentForm, SearchForm
from app.services import PostService, CategoryService
from datetime import datetime, timezone
import re
from sqlalchemy import func, or_

bp_public = Blueprint('public', __name__)

@bp_public.route('/health')
def health_check():
    """데이터베이스 연결 상태 확인"""
    try:
        db.session.execute('SELECT 1').scalar()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 503

@bp_public.route('/')
@bp_public.route('/posts')
def index():
    """메인 페이지 - 게시물 목록"""
    try:
        page = request.args.get('page', 1, type=int)
        category_id = request.args.get('category', type=int)
        search_query = request.args.get('q', '').strip()
        
        posts_query = Post.query.filter_by(is_published=True)
        
        if category_id:
            posts_query = posts_query.filter_by(category_id=category_id)
            
        if search_query:
            posts_query = posts_query.filter(
                or_(
                    Post.title.contains(search_query),
                    Post.content.contains(search_query),
                    Post.tags.contains(search_query)
                )
            )
        
        posts_query = posts_query.order_by(Post.published_at.desc())
        
        site_settings = SiteSetting.query.first()
        per_page = site_settings.posts_per_page if site_settings else 10
        
        posts = posts_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        categories = Category.query.all()
        
        return render_template(
            'public/post_list.html', 
            posts=posts, 
            categories=categories,
            current_category=category_id,
            search_query=search_query
        )
    except Exception as e:
        return render_template('public/post_list.html', posts=None, error=str(e))

@bp_public.route('/posts/<int:post_id>')
def post_detail(post_id):
    """게시물 상세 페이지"""
    try:
        post = Post.query.filter_by(id=post_id, is_published=True).first_or_404()
        
        # 조회수 증가
        post.views += 1
        db.session.commit()
        
        # 댓글 폼
        comment_form = CommentForm()
        
        # 이전/다음 게시물
        prev_post = Post.query.filter(
            Post.id < post_id, 
            Post.is_published == True
        ).order_by(Post.id.desc()).first()
        
        next_post = Post.query.filter(
            Post.id > post_id, 
            Post.is_published == True
        ).order_by(Post.id.asc()).first()
        
        return render_template(
            'public/post_detail.html',
            post=post,
            comment_form=comment_form,
            prev_post=prev_post,
            next_post=next_post
        )
    except Exception as e:
        abort(404)

@bp_public.route('/about')
def about():
    """소개 페이지"""
    try:
        site_settings = SiteSetting.query.first()
        return render_template('public/about.html', site_settings=site_settings)
    except Exception as e:
        return render_template('public/about.html', site_settings=None, error=str(e))

@bp_public.route('/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """댓글 추가"""
    try:
        post = Post.query.filter_by(id=post_id, is_published=True).first_or_404()
        form = CommentForm()
        
        if form.validate_on_submit():
            comment = Comment(
                nickname=form.nickname.data,
                content=form.content.data,
                post_id=post_id,
                ip_address=request.remote_addr,
                parent_id=form.parent_id.data if form.parent_id.data else None
            )
            db.session.add(comment)
            db.session.commit()
            
        return redirect(url_for('public.post_detail', post_id=post_id))
    except Exception as e:
        return redirect(url_for('public.post_detail', post_id=post_id))

@bp_public.route('/category/<int:category_id>')
def category_posts(category_id):
    """카테고리별 게시물 목록"""
    return redirect(url_for('public.index', category=category_id))

@bp_public.route('/search')
def search():
    """검색 결과"""
    query = request.args.get('q', '').strip()
    return redirect(url_for('public.index', q=query))
