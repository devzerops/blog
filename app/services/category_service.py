"""
카테고리 관련 비즈니스 로직을 처리하는 서비스 클래스입니다.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import func, desc

from app.models import Category, db, Post

class CategoryService:
    """카테고리 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    @staticmethod
    def get_all_categories(include_post_count: bool = False) -> List[Category]:
        """
        모든 카테고리를 조회합니다.
        
        Args:
            include_post_count: 각 카테고리의 포스트 수 포함 여부
            
        Returns:
            List[Category]: 카테고리 목록
        """
        query = Category.query.order_by(Category.name.asc())
        
        if include_post_count:
            # 각 카테고리의 포스트 수를 포함하여 조회
            categories = db.session.query(
                Category,
                func.count(Post.id).label('post_count')
            ).outerjoin(
                Post, 
                (Post.category_id == Category.id) & (Post.is_published == True)
            ).group_by(Category.id).order_by(Category.name.asc()).all()
            
            # 결과를 Category 객체와 post_count를 포함하는 딕셔너리로 변환
            result = []
            for category, post_count in categories:
                category.post_count = post_count
                result.append(category)
            return result
            
        return query.all()
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """
        카테고리 ID로 카테고리를 조회합니다.
        
        Args:
            category_id: 조회할 카테고리 ID
            
        Returns:
            Optional[Category]: 조회된 카테고리 객체 또는 None
        """
        return Category.query.get(category_id)
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """
        슬러그로 카테고리를 조회합니다.
        
        Args:
            slug: 조회할 카테고리 슬러그
            
        Returns:
            Optional[Category]: 조회된 카테고리 객체 또는 None
        """
        return Category.query.filter_by(slug=slug).first()
    
    @staticmethod
    def create_category(name: str, description: str = None, slug: str = None) -> Category:
        """
        새로운 카테고리를 생성합니다.
        
        Args:
            name: 카테고리 이름
            description: 카테고리 설명 (선택 사항)
            slug: URL 슬러그 (선택 사항, 미입력 시 이름에서 자동 생성)
            
        Returns:
            Category: 생성된 카테고리 객체
            
        Raises:
            ValueError: 이름이 이미 사용 중이거나 유효하지 않은 경우
        """
        if not name:
            raise ValueError("카테고리 이름은 필수 항목입니다.")
            
        # 이름 중복 확인
        if Category.query.filter(func.lower(Category.name) == name.lower()).first():
            raise ValueError(f"'{name}' 카테고리가 이미 존재합니다.")
        
        # 슬러그 생성 (미제공 시 이름에서 자동 생성)
        if not slug:
            from app.utils import slugify
            slug = slugify(name)
        
        # 슬러그 중복 확인
        if Category.query.filter_by(slug=slug).first():
            raise ValueError(f"'{slug}' 슬러그가 이미 사용 중입니다.")
        
        category = Category(
            name=name,
            description=description,
            slug=slug
        )
        
        db.session.add(category)
        db.session.commit()
        
        return category
    
    @staticmethod
    def update_category(category_id: int, **kwargs) -> Optional[Category]:
        """
        카테고리 정보를 업데이트합니다.
        
        Args:
            category_id: 업데이트할 카테고리 ID
            **kwargs: 업데이트할 필드 (name, description, slug 등)
            
        Returns:
            Optional[Category]: 업데이트된 카테고리 객체 또는 None (카테고리를 찾을 수 없는 경우)
            
        Raises:
            ValueError: 이름이나 슬러그가 이미 사용 중이거나 유효하지 않은 경우
        """
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            return None
            
        if 'name' in kwargs and kwargs['name'] != category.name:
            # 이름 중복 확인
            if Category.query.filter(
                func.lower(Category.name) == kwargs['name'].lower(),
                Category.id != category_id
            ).first():
                raise ValueError(f"'{kwargs['name']}' 카테고리가 이미 존재합니다.")
            category.name = kwargs['name']
        
        if 'slug' in kwargs and kwargs['slug'] != category.slug:
            # 슬러그 중복 확인
            if Category.query.filter(
                Category.slug == kwargs['slug'],
                Category.id != category_id
            ).first():
                raise ValueError(f"'{kwargs['slug']}' 슬러그가 이미 사용 중입니다.")
            category.slug = kwargs['slug']
        
        if 'description' in kwargs:
            category.description = kwargs['description']
        
        db.session.commit()
        return category
    
    @staticmethod
    def delete_category(category_id: int, move_to_category_id: int = None) -> bool:
        """
        카테고리를 삭제합니다.
        
        Args:
            category_id: 삭제할 카테고리 ID
            move_to_category_id: 삭제할 카테고리의 포스트를 이동시킬 대상 카테고리 ID (선택 사항)
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            ValueError: 카테고리를 찾을 수 없거나, 이동할 카테고리가 유효하지 않은 경우
        """
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            raise ValueError("카테고리를 찾을 수 없습니다.")
        
        # 이동할 카테고리 확인
        if move_to_category_id is not None:
            move_to_category = CategoryService.get_category_by_id(move_to_category_id)
            if not move_to_category or move_to_category.id == category_id:
                raise ValueError("유효하지 않은 대상 카테고리입니다.")
        
        # 카테고리 삭제 또는 포스트 이동
        if move_to_category_id is not None:
            # 포스트를 다른 카테고리로 이동
            Post.query.filter_by(category_id=category_id).update(
                {'category_id': move_to_category_id},
                synchronize_session=False
            )
        
        # 카테고리 삭제
        db.session.delete(category)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_popular_categories(limit: int = 5) -> List[Dict[str, Any]]:
        """
        인기 있는 카테고리 목록을 조회합니다.
        
        Args:
            limit: 조회할 카테고리 수
            
        Returns:
            List[Dict[str, Any]]: 카테고리 정보와 포스트 수를 포함한 리스트
        """
        categories = db.session.query(
            Category,
            func.count(Post.id).label('post_count')
        ).outerjoin(
            Post, 
            (Post.category_id == Category.id) & (Post.is_published == True)
        ).group_by(Category.id).order_by(
            desc('post_count'),
            Category.name
        ).limit(limit).all()
        
        result = []
        for category, post_count in categories:
            result.append({
                'category': category,
                'post_count': post_count
            })
            
        return result
    
    @staticmethod
    def get_category_with_posts(category_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        특정 카테고리와 해당 카테고리의 포스트 목록을 조회합니다.
        
        Args:
            category_id: 조회할 카테고리 ID
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            Dict[str, Any]: 카테고리 정보와 포스트 목록, 페이지네이션 정보
        """
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            raise ValueError("카테고리를 찾을 수 없습니다.")
        
        posts = Post.query.filter_by(
            category_id=category_id,
            is_published=True
        ).order_by(
            Post.published_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'category': category,
            'posts': posts.items,
            'page': page,
            'per_page': per_page,
            'total': posts.total,
            'pages': posts.pages
        }
    
    @staticmethod
    def get_or_create_category(name: str, **kwargs) -> Category:
        """
        카테고리가 존재하면 반환하고, 없으면 생성합니다.
        
        Args:
            name: 카테고리 이름
            **kwargs: 생성 시 사용할 추가 인자 (description, slug 등)
            
        Returns:
            Category: 조회되거나 생성된 카테고리 객체
        """
        category = Category.query.filter(
            func.lower(Category.name) == name.lower()
        ).first()
        
        if not category:
            return CategoryService.create_category(name, **kwargs)
            
        return category
