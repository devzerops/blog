"""
포스트 관련 비즈니스 로직을 처리하는 서비스 클래스입니다.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload

from app.models import Post, db, Category, User, Comment
from app.utils.image_utils import save_cover_image, delete_cover_image

class PostService:
    """포스트 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    @staticmethod
    def get_posts(page: int, per_page: int = 10, include_unpublished: bool = False) -> dict:
        """
        포스트 목록을 조회합니다.
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            include_unpublished: 미공개 포스트 포함 여부
            
        Returns:
            dict: 페이지네이션 정보와 포스트 목록
        """
        query = Post.query
        if not include_unpublished:
            query = query.filter(Post.is_published == True)
        
        posts = (query
                 .order_by(desc(Post.published_at if include_unpublished else Post.published_at))
                 .paginate(page=page, per_page=per_page, error_out=False))
        
        return {
            'items': posts.items,
            'page': page,
            'per_page': per_page,
            'total': posts.total,
            'pages': posts.pages
        }
    
    @staticmethod
    def get_post_by_id(post_id: int, include_comments: bool = False) -> Post:
        """
        ID로 단일 포스트를 조회합니다.
        
        Args:
            post_id: 조회할 포스트 ID
            include_comments: 댓글 포함 여부
            
        Returns:
            Post: 조회된 포스트 객체
        """
        query = Post.query
        
        if include_comments:
            query = query.options(joinedload(Post.comments).joinedload(Comment.author))
            
        return query.get_or_404(post_id)
    
    @staticmethod
    def create_post(post_data: dict, author_id: int, featured_image=None) -> Post:
        """
        새 포스트를 생성합니다.
        
        Args:
            post_data: 포스트 데이터 (제목, 내용, 카테고리 ID, 태그 등 포함)
            author_id: 작성자 ID
            featured_image: 대표 이미지 파일 (선택사항)
            
        Returns:
            Post: 생성된 포스트 객체
            
        Raises:
            ValueError: 유효하지 않은 카테고리 ID가 전달된 경우
        """
        # 썸네일 저장 로직
        thumbnail_filename = None
        if featured_image:
            _, thumbnail_filename = save_cover_image(featured_image)
        
        # 태그 처리
        tags_data = post_data.get('tags', [])
        if isinstance(tags_data, str):
            # 문자열인 경우 쉼표로 분리
            tags = ', '.join([t.strip() for t in tags_data.split(',') if t.strip()])
        else:
            # 이미 리스트인 경우
            tags = ', '.join([str(t).strip() for t in tags_data if str(t).strip()])
        
        # 카테고리 처리
        category_id = post_data.get('category_id')
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                raise ValueError("유효하지 않은 카테고리 ID입니다.")
        
        # 포스트 생성
        post_data_dict = {
            'title': post_data['title'],
            'content': post_data.get('content', ''),
            'user_id': author_id,  # author_id 대신 user_id 사용
            'is_published': post_data.get('is_published', False),
            'published_at': post_data.get('published_at'),  # 발행 시간 추가
            'category_id': category_id,
            'tags': tags  # 문자열로 저장
        }
        
        # 썸네일 파일명 가져오기 (post_data에서 제거하지 않고 그대로 사용)
        thumbnail_filename = post_data.get('thumbnail_filename')
        
        # 썸네일 파일명이 있는 경우에만 추가
        if thumbnail_filename:
            post_data_dict['thumbnail_filename'] = thumbnail_filename
            
        post = Post(**post_data_dict)
        db.session.add(post)
        db.session.commit()
        
        return post
    
    @staticmethod
    def update_post(post_id: int, post_data: dict, featured_image=None) -> Post:
        """
        기존 포스트를 업데이트합니다.
        
        Args:
            post_id: 업데이트할 포스트 ID
            post_data: 업데이트할 포스트 데이터
            featured_image: 새로운 대표 이미지 (선택사항)
            
        Returns:
            Post: 업데이트된 포스트 객체
        """
        post = Post.query.get_or_404(post_id)
        
        # 이미지 업데이트
        if featured_image:
            try:
                # 기존 썸네일 삭제
                if post.thumbnail_filename:
                    delete_cover_image(post.thumbnail_filename)
                
                # 새 썸네일 이미지 저장
                _, thumbnail_filename = save_cover_image(featured_image)
                if not thumbnail_filename:
                    raise ValueError('이미지 처리에 실패했습니다. 다른 이미지로 시도해주세요.')
                
                # 썸네일 파일명 업데이트
                post.thumbnail_filename = thumbnail_filename
                current_app.logger.info(f'썸네일 이미지가 성공적으로 업데이트되었습니다: {thumbnail_filename}')
                
            except Exception as e:
                current_app.logger.error(f'이미지 업데이트 중 오류: {str(e)}', exc_info=True)
                raise ValueError(f'이미지 업데이트 중 오류가 발생했습니다: {str(e)}')
        
        # 태그 업데이트
        if 'tags' in post_data:
            tags_data = post_data['tags']
            if isinstance(tags_data, str):
                # 문자열인 경우 쉼표로 분리
                post.tags = ', '.join([t.strip() for t in tags_data.split(',') if t.strip()])
            else:
                    # 이미 리스트인 경우
                post.tags = ', '.join([str(t).strip() for t in tags_data if str(t).strip()])
        else:
            post.tags = ''
        
        # 발행 상태 업데이트
        if 'is_published' in post_data:
            post.is_published = post_data['is_published']
            # 발행 상태가 True로 변경되었고, published_at이 설정되지 않은 경우에만 현재 시간으로 설정
            if post.is_published and not post.published_at:
                post.published_at = post_data.get('published_at', datetime.utcnow())
            # 발행 상태가 False로 변경된 경우 published_at을 None으로 설정
            elif not post.is_published:
                post.published_at = None
        
        # 카테고리 업데이트
        if 'category_id' in post_data and post_data['category_id'] is not None:
            try:
                category_id = int(post_data['category_id'])
                if category_id > 0:  # 유효한 카테고리 ID인 경우에만 처리
                    category = Category.query.get(category_id)
                    if category:
                        post.category = category
                else:
                    post.category = None  # 0 또는 음수인 경우 카테고리 제거
            except (ValueError, TypeError):
                # 유효하지 않은 category_id인 경우 무시
                current_app.logger.warning(f'Invalid category_id: {post_data["category_id"]}')
                post.category = None
        
        # 기타 필드 업데이트
        for field in ['title', 'content', 'is_published', 'meta_description', 'slug', 
                    'image_filename', 'thumbnail_filename', 'alt_text', 'video_embed_url']:
            if field in post_data and post_data[field] is not None:
                setattr(post, field, post_data[field])
        
        if post.is_published and not post.published_at:
            post.published_at = datetime.utcnow()
            
        db.session.commit()
        return post
    
    @staticmethod
    def delete_post(post_id: int) -> bool:
        """
        포스트를 삭제합니다.
        
        Args:
            post_id: 삭제할 포스트 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        post = Post.query.get_or_404(post_id)
        
        # 썸네일 이미지 삭제
        if post.thumbnail_filename:
            delete_cover_image(None, post.thumbnail_filename)
        
        # 댓글 삭제
        Comment.query.filter_by(post_id=post_id).delete()
        
        # 태그 관계 제거 (태그 자체는 삭제하지 않음)
        post.tags = []
        
        db.session.delete(post)
        db.session.commit()
        return True
    
    @staticmethod
    def get_popular_posts(limit: int = 5) -> List[Post]:
        """
        인기 있는 포스트 목록을 조회합니다.
        
        Args:
            limit: 조회할 포스트 수
            
        Returns:
            List[Post]: 인기 포스트 목록
        """
        return (Post.query
                .filter(Post.is_published == True)
                .order_by(Post.view_count.desc())
                .limit(limit)
                .all())
    
    @staticmethod
    def get_related_posts(post_id: int, limit: int = 3) -> List[Post]:
        """
        관련 포스트 목록을 조회합니다.
        
        Args:
            post_id: 기준 포스트 ID
            limit: 조회할 포스트 수
            
        Returns:
            List[Post]: 관련 포스트 목록
        """
        post = Post.query.get_or_404(post_id)
        
        # 같은 카테고리의 다른 포스트 조회
        related = (Post.query
                  .filter(
                      Post.id != post_id,
                      Post.is_published == True,
                      Post.category_id == post.category_id
                  )
                  .order_by(Post.published_at.desc())
                  .limit(limit)
                  .all())
        
        # 같은 카테고리의 포스트가 부족하면 최신 포스트로 채움
        if len(related) < limit:
            additional = (Post.query
                        .filter(
                            Post.id != post_id,
                            Post.is_published == True,
                            Post.category_id != post.category_id
                        )
                        .order_by(Post.published_at.desc())
                        .limit(limit - len(related))
                        .all())
            related.extend(additional)
        
        return related
    
    @staticmethod
    def increment_view_count(post_id: int) -> None:
        """
        포스트 조회수를 증가시킵니다.
        
        Args:
            post_id: 조회수를 증가시킬 포스트 ID
        """
        post = Post.query.get(post_id)
        if post:
            post.view_count = Post.view_count + 1
            db.session.commit()
    
    @staticmethod
    def get_archive_months() -> List[Dict[str, Any]]:
        """
        포스트가 있는 월별 아카이브 목록을 조회합니다.
        
        Returns:
            List[Dict[str, Any]]: 월별 아카이브 정보 리스트
        """
        return (db.session.query(
                    func.date_format(Post.published_at, '%Y-%m').label('month'),
                    func.count(Post.id).label('count')
                )
                .filter(Post.is_published == True)
                .group_by('month')
                .order_by(desc('month'))
                .all())
    
    @staticmethod
    def get_posts_by_month(year: int, month: int, page: int = 1, per_page: int = 10) -> dict:
        """
        특정 년월에 작성된 포스트 목록을 조회합니다.
        
        Args:
            year: 년도
            month: 월
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            dict: 페이지네이션 정보와 포스트 목록
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
            
        query = Post.query.filter(
            Post.published_at >= start_date,
            Post.published_at < end_date,
            Post.is_published == True
        )
        
        posts = query.order_by(desc(Post.published_at))\
                   .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': posts.items,
            'page': page,
            'per_page': per_page,
            'total': posts.total,
            'pages': posts.pages,
            'year': year,
            'month': month
        }
