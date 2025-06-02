"""
파일 처리 관련 유틸리티 함수 모음
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
import io

def allowed_file(filename, allowed_extensions=None):
    """
    파일 확장자가 허용된 확장자 목록에 있는지 확인합니다.
    
    Args:
        filename: 확인할 파일명
        allowed_extensions: 허용할 파일 확장자 집합 (기본값: app.config['ALLOWED_EXTENSIONS'])
        
    Returns:
        bool: 파일이 허용된 확장자를 가지고 있으면 True, 아니면 False
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_unique_filename(filename):
    """
    안전한 고유한 파일명을 생성합니다.
    
    Args:
        filename: 원본 파일명
        
    Returns:
        tuple: (안전한 원본 파일명, 고유한 저장 파일명)
    """
    original_filename = secure_filename(filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    return original_filename, unique_filename

def save_uploaded_file(file, subfolder='', resize=None):
    """
    업로드된 파일을 저장하고 파일 정보를 반환합니다.
    
    Args:
        file: 업로드된 파일 객체 (Werkzeug FileStorage)
        subfolder: 저장할 서브폴더 (예: 'thumbnails', 'uploads' 등)
        resize: (width, height) 튜플로 이미지 리사이즈 (선택사항)
        
    Returns:
        dict: 저장된 파일 정보 (original_name, saved_name, file_path, file_size, mime_type)
        
    Raises:
        ValueError: 파일이 유효하지 않은 경우
    """
    if not file or file.filename == '':
        raise ValueError('No selected file')
        
    if not allowed_file(file.filename):
        raise ValueError('File type not allowed')
    
    # 파일명 보안 처리
    original_name, saved_name = secure_unique_filename(file.filename)
    
    # 저장 경로 설정
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, saved_name)
    
    # 이미지 리사이즈가 필요한 경우
    if resize and file.content_type.startswith('image/'):
        try:
            img = Image.open(file.stream)
            img.thumbnail(resize, Image.LANCZOS)
            
            # 투명도 유지를 위해 RGB로 변환
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            img.save(file_path, optimize=True, quality=85)
            file_size = os.path.getsize(file_path)
        except Exception as e:
            current_app.logger.error(f'Error processing image: {e}')
            # 이미지 처리 실패 시 원본 저장
            file.stream.seek(0)  # 스트림 위치 초기화
            file.save(file_path)
            file_size = os.path.getsize(file_path)
    else:
        file.save(file_path)
        file_size = os.path.getsize(file_path)
    
    return {
        'original_name': original_name,
        'saved_name': saved_name,
        'file_path': file_path,
        'file_size': file_size,
        'mime_type': file.content_type
    }


def delete_uploaded_file(filename, subfolder=''):
    """
    업로드된 파일을 삭제합니다.
    
    Args:
        filename: 삭제할 파일명 (서브폴더 제외)
        subfolder: 파일이 위치한 서브폴더 (선택사항)
        
    Returns:
        bool: 삭제 성공 시 True, 실패 시 False
        
    Raises:
        ValueError: 파일이 존재하지 않는 경우
        OSError: 파일 삭제 중 오류가 발생한 경우
    """
    if not filename:
        raise ValueError('No filename provided')
    
    # 보안을 위해 파일명에서 상위 디렉토리 접근 방지
    filename = os.path.basename(filename)
    
    # 파일 경로 구성
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
    
    # 파일 존재 여부 확인
    if not os.path.exists(file_path):
        raise ValueError(f'File not found: {filename}')
    
    try:
        os.remove(file_path)
        current_app.logger.info(f'Successfully deleted file: {file_path}')
        return True
    except OSError as e:
        current_app.logger.error(f'Error deleting file {file_path}: {e}')
        raise OSError(f'Failed to delete file: {filename}')
    except Exception as e:
        current_app.logger.error(f'Unexpected error deleting file {file_path}: {e}')
        raise
