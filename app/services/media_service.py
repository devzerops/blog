"""
미디어 파일 관련 비즈니스 로직을 처리하는 서비스 클래스입니다.
"""
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
import shutil
from pathlib import Path

from flask import current_app, url_for
import os
from werkzeug.utils import secure_filename

from app.models import db, Media

# 파일 확장자 검사
def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 파일 확장자 추출
def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

class MediaService:
    """미디어 파일 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    # 허용되는 이미지 확장자
    IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # 허용되는 문서 확장자
    DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'}
    
    # 허용되는 아카이브 확장자
    ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz'}
    
    @staticmethod
    def get_all_media(page: int = 1, per_page: int = 20, media_type: str = None) -> Dict[str, Any]:
        """
        모든 미디어 파일을 조회합니다.
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            media_type: 미디어 유저 필터 (image, document, archive, other)
            
        Returns:
            Dict[str, Any]: 미디어 목록과 페이지네이션 정보
        """
        query = Media.query
        
        # 미디어 유저별 필터링
        if media_type == 'image':
            query = query.filter(Media.file_type == 'image')
        elif media_type == 'document':
            query = query.filter(Media.file_type == 'document')
        elif media_type == 'archive':
            query = query.filter(Media.file_type == 'archive')
        elif media_type == 'other':
            query = query.filter(Media.file_type == 'other')
        
        # 최신순 정렬
        media_pagination = query.order_by(Media.uploaded_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': media_pagination.items,
            'page': page,
            'per_page': per_page,
            'total': media_pagination.total,
            'pages': media_pagination.pages,
            'media_type': media_type
        }
    
    @staticmethod
    def get_media_by_id(media_id: int) -> Optional[Media]:
        """
        미디어 ID로 미디어를 조회합니다.
        
        Args:
            media_id: 조회할 미디어 ID
            
        Returns:
            Optional[Media]: 조회된 미디어 객체 또는 None
        """
        return Media.query.get(media_id)
    
    @classmethod
    def upload_media(cls, file, upload_dir: str = None, resize_images: bool = True) -> Media:
        """
        미디어 파일을 업로드하고 데이터베이스에 저장합니다.
        
        Args:
            file: 업로드할 파일 객체 (Werkzeug FileStorage)
            upload_dir: 업로드할 디렉토리 (기본값: app.config['UPLOAD_FOLDER'])
            resize_images: 이미지 리사이즈 여부
            
        Returns:
            Media: 생성된 미디어 객체
            
        Raises:
            ValueError: 파일이 유효하지 않은 경우
        """
        if not file or file.filename == '':
            raise ValueError("파일이 선택되지 않았습니다.")
        
        filename = secure_filename(file.filename)
        if not filename:
            raise ValueError("유효하지 않은 파일명입니다.")
        
        # 파일 확장자 확인
        file_ext = get_file_extension(filename)
        if not file_ext or not allowed_file(filename):
            raise ValueError("허용되지 않는 파일 형식입니다.")
        
        # 업로드 디렉토리 설정
        if upload_dir is None:
            upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
        
        # 업로드 디렉토리가 없으면 생성
        os.makedirs(upload_dir, exist_ok=True)
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        filepath = os.path.join(upload_dir, unique_filename)
        
        # 파일 저장
        file.save(filepath)
        
        # 파일 정보 가져오기
        file_size = os.path.getsize(filepath)
        file_type = cls._get_file_type(file_ext)
        
        # 이미지인 경우 추가 처리
        width = height = None
        if file_type == 'image':
            try:
                with PILImage.open(filepath) as img:
                    width, height = img.size
                    
                    # 이미지 리사이즈 (선택 사항)
                    if resize_images and (width > 1200 or height > 1200):
                        img.thumbnail((1200, 1200), PILImage.LANCZOS)
                        img.save(filepath, optimize=True, quality=85)
                        file_size = os.path.getsize(filepath)
                        width, height = img.size
            except Exception as e:
                current_app.logger.error(f"이미지 처리 중 오류 발생: {e}")
        
        # 미디어 정보 저장
        media = Media(
            original_filename=filename,
            stored_filename=unique_filename,
            file_size=file_size,
            file_type=file_type,
            mime_type=file.content_type,
            width=width,
            height=height,
            alt_text=os.path.splitext(filename)[0]  # 기본 alt 텍스트로 파일명 사용
        )
        
        db.session.add(media)
        db.session.commit()
        
        return media
    
    @staticmethod
    def update_media(media_id: int, **kwargs) -> Optional[Media]:
        """
        미디어 정보를 업데이트합니다.
        
        Args:
            media_id: 업데이트할 미디어 ID
            **kwargs: 업데이트할 필드 (alt_text, caption, description 등)
            
        Returns:
            Optional[Media]: 업데이트된 미디어 객체 또는 None (미디어를 찾을 수 없는 경우)
        """
        media = MediaService.get_media_by_id(media_id)
        if not media:
            return None
        
        # 업데이트할 필드 설정
        for key, value in kwargs.items():
            if hasattr(media, key):
                setattr(media, key, value)
        
        media.updated_at = datetime.utcnow()
        db.session.commit()
        
        return media
    
    @staticmethod
    def delete_media(media_id: int) -> bool:
        """
        미디어 파일을 삭제합니다.
        
        Args:
            media_id: 삭제할 미디어 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        media = MediaService.get_media_by_id(media_id)
        if not media:
            return False
        
        # 파일 삭제
        try:
            filepath = os.path.join(
                current_app.root_path,
                current_app.config['UPLOAD_FOLDER'],
                media.stored_filename
            )
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
                # 썸네일이 있는 경우 삭제
                thumb_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], 'thumbnails')
                thumb_path = os.path.join(thumb_dir, media.stored_filename)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
        except Exception as e:
            current_app.logger.error(f"미디어 파일 삭제 중 오류 발생: {e}")
            return False
        
        # 데이터베이스에서 삭제
        db.session.delete(media)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_media_url(media: Media, thumbnail: bool = False) -> str:
        """
        미디어 파일의 URL을 반환합니다.
        
        Args:
            media: 미디어 객체
            thumbnail: 썸네일 URL을 반환할지 여부
            
        Returns:
            str: 미디어 파일의 URL
        """
        if not media:
            return ''
            
        if thumbnail and media.file_type == 'image':
            # 썸네일 URL 생성 (실제 구현에서는 썸네일 생성 로직이 필요함)
            return url_for('static', filename=f"uploads/thumbnails/{media.stored_filename}", _external=True)
        
        return url_for('static', filename=f"uploads/{media.stored_filename}", _external=True)
    
    @classmethod
    def _get_file_type(cls, file_ext: str) -> str:
        """
        파일 확장자에 따라 파일 유형을 반환합니다.
        
        Args:
            file_ext: 파일 확장자 (.jpg, .pdf 등)
            
        Returns:
            str: 파일 유형 (image, document, archive, other)
        """
        ext = file_ext.lower().lstrip('.')
        
        if ext in cls.IMAGE_EXTENSIONS:
            return 'image'
        elif ext in cls.DOCUMENT_EXTENSIONS:
            return 'document'
        elif ext in cls.ARCHIVE_EXTENSIONS:
            return 'archive'
        else:
            return 'other'
    
    @staticmethod
    def cleanup_unused_media() -> Tuple[int, int]:
        """
        사용되지 않는 미디어 파일을 정리합니다.
        
        Returns:
            Tuple[int, int]: (삭제된 파일 수, 총 파일 수)
        """
        # 미디어 디렉토리 경로
        upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
        thumb_dir = os.path.join(upload_dir, 'thumbnails')
        
        # 데이터베이스에 등록된 모든 미디어 파일명 가져오기
        stored_filenames = {m.stored_filename for m in Media.query.all()}
        
        # 실제 파일 시스템의 파일 목록 가져오기
        actual_files = set()
        for root, _, files in os.walk(upload_dir):
            for file in files:
                if file.startswith('.'):  # 숨김 파일 제외
                    continue
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath):
                    # 업로드 디렉토리 내의 파일만 처리
                    rel_path = os.path.relpath(filepath, upload_dir)
                    if not rel_path.startswith('..'):
                        actual_files.add(rel_path)
        
        # 데이터베이스에 없지만 파일 시스템에 있는 파일 찾기
        orphaned_files = actual_files - stored_filenames
        
        # 고아 파일 삭제
        deleted_count = 0
        for filename in orphaned_files:
            try:
                filepath = os.path.join(upload_dir, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted_count += 1
                    
                    # 썸네일도 삭제 시도
                    thumb_path = os.path.join(thumb_dir, os.path.basename(filename))
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
            except Exception as e:
                current_app.logger.error(f"파일 삭제 중 오류 발생 ({filename}): {e}")
        
        return deleted_count, len(orphaned_files)
