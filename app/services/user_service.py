"""
사용자 관련 비즈니스 로직을 처리하는 서비스 클래스입니다.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash
from sqlalchemy import or_

from app.models import User, db

class UserService:
    """사용자 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        사용자 ID로 사용자 정보를 조회합니다.
        
        Args:
            user_id: 조회할 사용자 ID
            
        Returns:
            Optional[User]: 조회된 사용자 객체 또는 None
        """
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        사용자명으로 사용자 정보를 조회합니다.
        
        Args:
            username: 조회할 사용자명
            
        Returns:
            Optional[User]: 조회된 사용자 객체 또는 None
        """
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        이메일로 사용자 정보를 조회합니다.
        
        Args:
            email: 조회할 이메일 주소
            
        Returns:
            Optional[User]: 조회된 사용자 객체 또는 None
        """
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """
        사용자 인증을 수행합니다.
        
        Args:
            username: 사용자명 또는 이메일
            password: 비밀번호
            
        Returns:
            Optional[User]: 인증된 사용자 객체 또는 None
        """
        user = User.query.filter(
            or_(
                User.username == username,
                User.email == username
            )
        ).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        return None
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> User:
        """
        새로운 사용자를 생성합니다.
        
        Args:
            user_data: 사용자 생성 데이터
                - username: 사용자명
                - email: 이메일 주소
                - password: 비밀번호 (평문)
                - **kwargs: 기타 사용자 속성
                
        Returns:
            User: 생성된 사용자 객체
            
        Raises:
            ValueError: 필수 필드가 누락된 경우
        """
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValueError(f"{field}은(는) 필수 항목입니다.")
        
        if UserService.get_user_by_username(user_data['username']):
            raise ValueError("이미 사용 중인 사용자명입니다.")
            
        if UserService.get_user_by_email(user_data['email']):
            raise ValueError("이미 사용 중인 이메일 주소입니다.")
        
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=generate_password_hash(user_data['password'])
        )
        
        # 추가 필드 설정
        for key, value in user_data.items():
            if hasattr(user, key) and key not in ['password', 'password_hash']:
                setattr(user, key, value)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def update_user(user_id: int, user_data: Dict[str, Any]) -> User:
        """
        사용자 정보를 업데이트합니다.
        
        Args:
            user_id: 업데이트할 사용자 ID
            user_data: 업데이트할 사용자 데이터
                - username: 새 사용자명 (선택 사항)
                - email: 새 이메일 주소 (선택 사항)
                - password: 새 비밀번호 (선택 사항, 평문)
                - **kwargs: 기타 업데이트할 사용자 속성
                
        Returns:
            User: 업데이트된 사용자 객체
            
        Raises:
            ValueError: 사용자를 찾을 수 없거나 유효하지 않은 데이터인 경우
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 사용자명 업데이트
        if 'username' in user_data and user_data['username'] != user.username:
            if UserService.get_user_by_username(user_data['username']):
                raise ValueError("이미 사용 중인 사용자명입니다.")
            user.username = user_data['username']
        
        # 이메일 업데이트
        if 'email' in user_data and user_data['email'] != user.email:
            if UserService.get_user_by_email(user_data['email']):
                raise ValueError("이미 사용 중인 이메일 주소입니다.")
            user.email = user_data['email']
        
        # 비밀번호 업데이트
        if 'password' in user_data and user_data['password']:
            user.set_password(user_data['password'])
        
        # 기타 필드 업데이트
        for key, value in user_data.items():
            if hasattr(user, key) and key not in ['password', 'password_hash', 'username', 'email']:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """
        사용자 계정을 삭제합니다.
        
        Args:
            user_id: 삭제할 사용자 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 여기서는 간단히 삭제하지만, 실제로는 연관된 데이터도 함께 처리해야 할 수 있음
        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """
        사용자 통계 정보를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 사용자 통계 정보
        """
        from app.models import Post, Comment
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 사용자 작성 포스트 수
        post_count = Post.query.filter_by(author_id=user_id).count()
        
        # 사용자 작성 댓글 수
        comment_count = Comment.query.filter_by(user_id=user_id).count()
        
        # 최근 활동 일자
        last_activity = user.last_login or user.member_since
        
        return {
            'post_count': post_count,
            'comment_count': comment_count,
            'member_since': user.member_since,
            'last_activity': last_activity,
            'is_admin': user.is_admin
        }
    
    @staticmethod
    def search_users(query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        사용자를 검색합니다.
        
        Args:
            query: 검색어 (사용자명 또는 이메일)
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            Dict[str, Any]: 검색 결과와 페이지네이션 정보
        """
        search = f"%{query}%"
        query = User.query.filter(
            or_(
                User.username.ilike(search),
                User.email.ilike(search)
            )
        )
        
        users = query.order_by(User.username.asc())\
                   .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': users.items,
            'page': page,
            'per_page': per_page,
            'total': users.total,
            'pages': users.pages,
            'query': query
        }
    
    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> bool:
        """
        사용자 비밀번호를 변경합니다.
        
        Args:
            user_id: 사용자 ID
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            bool: 비밀번호 변경 성공 여부
            
        Raises:
            ValueError: 현재 비밀번호가 일치하지 않는 경우
        """
        user = UserService.get_user_by_id(user_id)
        if not user or not user.check_password(current_password):
            raise ValueError("현재 비밀번호가 일치하지 않습니다.")
        
        user.set_password(new_password)
        db.session.commit()
        return True
    
    @staticmethod
    def reset_password_request(email: str) -> bool:
        """
        비밀번호 재설정 요청을 처리합니다.
        
        Args:
            email: 비밀번호를 재설정할 사용자의 이메일
            
        Returns:
            bool: 요청 처리 성공 여부
        """
        user = UserService.get_user_by_email(email)
        if not user:
            # 보안을 위해 사용자 존재 여부를 노출하지 않음
            return True
        
        # 여기서는 단순히 True를 반환하지만, 실제로는 이메일 발송 로직이 필요함
        # 예: send_password_reset_email(user)
        return True
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        비밀번호를 재설정합니다.
        
        Args:
            token: 비밀번호 재설정 토큰
            new_password: 새 비밀번호
            
        Returns:
            bool: 비밀번호 재설정 성공 여부
            
        Raises:
            ValueError: 유효하지 않거나 만료된 토큰인 경우
        """
        # 실제 구현에서는 토큰 검증 로직이 필요함
        # 예: user = User.verify_reset_password_token(token)
        # if not user:
        #     raise ValueError("유효하지 않거나 만료된 토큰입니다.")
        # 
        # user.set_password(new_password)
        # db.session.commit()
        # return True
        
        # 여기서는 단순히 예외를 발생시키지 않음
        return True
