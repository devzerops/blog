
from flask import request
from app.models import PageView
from app.database import db

def register_middleware_handlers(app):
    """미들웨어 핸들러 등록"""
    
    @app.after_request
    def log_request(response):
        """HTTP 요청 로깅"""
        # 정적 파일 요청은 로깅에서 제외
        if request.path.startswith('/static/'):
            return response
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string.split(' ')[0] if request.user_agent else 'Unknown',
            'response_size': None
        }
        
        # 응답 크기 기록
        if not response.direct_passthrough:
            try:
                log_data['response_size'] = len(response.get_data())
            except Exception as e:
                app.logger.warning(f'응답 크기 가져오기 실패: {str(e)}')
        
        # 에러 상태 코드는 WARNING 레벨로 로깅
        if 400 <= response.status_code < 600:
            app.logger.warning('HTTP Request: %s', log_data)
        else:
            app.logger.info('HTTP Request: %s', log_data)
        
        return response
    
    @app.after_request
    def log_page_view(response):
        """페이지 뷰 로깅"""
        # 정적 파일이나 에러 응답은 제외
        if request.path.startswith('/static') or response.status_code // 100 != 2:
            return response
        
        try:
            page_view = PageView(
                path=request.path,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                post_id=None  # 필요시 라우트에서 설정
            )
            db.session.add(page_view)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"페이지 뷰 로깅 오류: {e}")
            db.session.rollback()
        
        return response
