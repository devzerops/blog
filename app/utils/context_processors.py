
import datetime
from app.models import SiteSetting
from app.services import PostService, UserService, CategoryService, MediaService

def register_context_processors(app):
    """컨텍스트 프로세서 등록"""
    
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.datetime.now(datetime.timezone.utc).year}
    
    @app.context_processor
    def inject_site_settings():
        try:
            settings = SiteSetting.query.first()
            return {'site_settings': settings}
        except Exception as e:
            app.logger.warning(f"사이트 설정 로딩 실패: {e}")
            return {'site_settings': None}
    
    @app.context_processor
    def inject_services():
        return {
            'post_service': PostService(),
            'user_service': UserService(),
            'category_service': CategoryService(),
            'media_service': MediaService()
        }
