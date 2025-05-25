import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app, session, redirect, url_for, flash
from app.models import User

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 세션에서 토큰 확인
        token = session.get('admin_token')
        
        # 세션에 토큰이 없으면 Authorization 헤더 확인 (API 및 이미지 업로드용)
        if not token and request.headers.get('Authorization'):
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                current_app.logger.info('Using token from Authorization header')
        
        # 토큰이 여전히 없으면 로그인 페이지로 리디렉션
        if not token:
            # API 요청인 경우 JSON 응답 반환
            if request.is_json or request.path.endswith(('upload_editor_image')):
                return jsonify({'error': 'Authentication required', 'message': '인증이 필요합니다'}), 401
            
            # 일반 페이지 요청인 경우 로그인 페이지로 리디렉션
            flash('로그인이 필요합니다. 이 페이지에 접근하려면 먼저 로그인해주세요.', 'warning')
            return redirect(url_for('auth.login_page', next=request.url))
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                flash('사용자를 찾을 수 없습니다. 다시 로그인해주세요.', 'danger')
                session.pop('admin_token', None)
                return redirect(url_for('auth.login_page'))
        except jwt.ExpiredSignatureError:
            flash('세션이 만료되었습니다. 다시 로그인해주세요.', 'warning')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page', next=request.url))
        except jwt.InvalidTokenError:
            flash('유효하지 않은 토큰입니다. 다시 로그인해주세요.', 'danger')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            current_app.logger.error(f"Token validation error: {e}")
            flash('인증 중 오류가 발생했습니다. 다시 로그인해주세요.', 'danger')
            session.pop('admin_token', None)
            return redirect(url_for('auth.login_page'))
        
        return f(current_user, *args, **kwargs)
    return decorated_function

def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'iat': datetime.now(timezone.utc), # Issued at time
        'exp': datetime.now(timezone.utc) + timedelta(seconds=current_app.config.get('JWT_EXPIRATION_SECONDS', 3600))
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def get_current_user_if_logged_in():
    token = session.get('admin_token')
    if not token:
        return None
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = User.query.get(data['user_id'])
        return current_user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
        # Token expired, invalid, or user_id not in token payload
        return None
    except Exception as e:
        current_app.logger.error(f"Error decoding token for optional login: {e}")
        return None

# Alias for admin routes, can be expanded later if different admin roles/permissions are needed
admin_required = token_required
