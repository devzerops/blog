
import logging
from flask import request

def setup_logging(app):
    """로깅 설정"""
    app.logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)
    
    # 서드파티 로거 레벨 설정
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('PIL').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('markdown').setLevel(logging.ERROR)
