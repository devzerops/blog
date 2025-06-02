"""
Admin site statistics routes.
Contains routes for viewing site analytics and statistics.
"""

from datetime import datetime, timedelta
from flask import render_template, current_app
from sqlalchemy import func, desc, and_

from app.database import db
from app.models import Post, Comment, PageView
from app.auth import admin_required
from app.routes.admin import bp_admin


@bp_admin.route('/site-stats')
@admin_required
def site_stats(current_user):
    """Site statistics dashboard"""
    # Get current date and set time range for today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get statistics for today
    total_views_today = db.session.query(func.count(PageView.id))\
                               .filter(PageView.timestamp.between(today_start, today_end)).scalar()
    
    total_comments_today = db.session.query(func.count(Comment.id))\
                                  .filter(Comment.created_at.between(today_start, today_end)).scalar()
    
    total_posts_today = db.session.query(func.count(Post.id))\
                               .filter(Post.created_at.between(today_start, today_end)).scalar()
    
    # Get total statistics
    total_views = db.session.query(func.count(PageView.id)).scalar()
    total_comments = db.session.query(func.count(Comment.id)).scalar()
    total_posts = db.session.query(func.count(Post.id)).scalar()
    published_posts = db.session.query(func.count(Post.id)).filter(Post.is_published == True).scalar()
    
    # Calculate total post views (sum of views from all posts)
    total_post_views = db.session.query(func.coalesce(func.sum(Post.views), 0)).scalar()
    
    # Get most viewed posts
    most_viewed_posts = db.session.query(
        Post, func.count(PageView.id).label('views')
    ).join(PageView, PageView.post_id == Post.id)\
     .group_by(Post.id)\
     .order_by(desc('views'))\
     .limit(5).all()
    
    # Get most commented posts
    most_commented_posts = db.session.query(
        Post, func.count(Comment.id).label('comments')
    ).join(Comment, Comment.post_id == Post.id)\
     .group_by(Post.id)\
     .order_by(desc('comments'))\
     .limit(5).all()
    
    # Get recent visitor trends (last 7 days)
    seven_days_ago = today - timedelta(days=7)
    visitor_trend = []
    
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        unique_visitors = db.session.query(func.count(func.distinct(PageView.ip_address)))\
                                .filter(PageView.timestamp.between(day_start, day_end)).scalar()
        
        visitor_trend.append({
            'date': day.strftime('%Y-%m-%d'),
            'visitors': unique_visitors
        })
    
    # Get current active users (viewed page in last 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    active_users_approx = db.session.query(func.count(func.distinct(PageView.ip_address)))\
                                  .filter(PageView.timestamp >= five_minutes_ago).scalar()

    return render_template('admin/admin_site_stats.html', 
                           title='사이트 통계',
                           total_views_today=total_views_today,
                           total_comments_today=total_comments_today,
                           total_posts_today=total_posts_today,
                           total_views=total_views,
                           total_comments=total_comments,
                           total_posts=total_posts,
                           published_posts=published_posts,
                           total_post_views=total_post_views,
                           most_viewed_posts=most_viewed_posts,
                           most_commented_posts=most_commented_posts,
                           visitor_trend=visitor_trend,
                           active_users=active_users_approx,
                           current_user=current_user)
