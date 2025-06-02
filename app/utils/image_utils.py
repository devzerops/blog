import os
import logging
from pathlib import Path
from PIL import Image, ImageOps, ImageFile
import secrets
import imghdr
from flask import current_app
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger(__name__)

# Allow PIL to load truncated images (useful for some corrupted but viewable images)
ImageFile.LOAD_TRUNCATED_IMAGES = True

def validate_image(file_storage):
    """
    Validate the uploaded image file.
    
    Args:
        file_storage: FileStorage object from Flask
        
    Returns:
        tuple: (original_filename, file_extension, mime_type)
        
    Raises:
        ValueError: If the file is invalid
    """
    if not file_storage or not hasattr(file_storage, 'filename') or not file_storage.filename:
        raise ValueError('No file selected')

    # Secure the filename
    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError('Invalid filename')

    # Check file size (max 30MB)
    file_storage.seek(0, 2)  # Go to end of file
    file_size = file_storage.tell()
    file_storage.seek(0)  # Reset file pointer
    
    if file_size == 0:
        raise ValueError('업로드된 파일이 비어 있습니다')
    max_size_mb = 30
    if file_size > max_size_mb * 1024 * 1024:  # 30MB
        raise ValueError(f'파일 크기가 {max_size_mb}MB를 초과합니다. 현재 파일 크기: {file_size / (1024 * 1024):.2f}MB')

    # Check file type
    mime_type = imghdr.what(file_storage)
    if not mime_type or mime_type.lower() not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
        raise ValueError('Unsupported file type. Only JPEG, PNG, GIF, and WebP are allowed')
    
    # Get file extension based on mime type
    ext = f".{mime_type}" if mime_type != 'jpeg' else '.jpg'
    
    return filename, ext, mime_type

def process_image(img, target_size):
    """
    Process image with better quality and performance.
    
    Args:
        img: PIL Image object
        target_size: Tuple of (width, height) for the target size
        
    Returns:
        PIL Image: Processed image
    """
    try:
        # Auto-orient based on EXIF data first
        img = ImageOps.exif_transpose(img)
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate dimensions maintaining aspect ratio
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            # Image is wider than target
            new_width = target_size[0]
            new_height = int(target_size[0] / img_ratio)
        else:
            # Image is taller than target
            new_height = target_size[1]
            new_width = int(target_size[1] * img_ratio)
        
        # High-quality resize using LANCZOS (a high-quality downsampling filter)
        if (new_width, new_height) != img.size:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to process image: {str(e)}")

def save_cover_image(form_picture, output_size=(1200, 630), thumbnail_size=(300, 200)):
    """
    Save the uploaded cover image and generate a thumbnail.
    
    Args:
        form_picture: FileStorage object from Flask
        output_size: Tuple of (width, height) for the main image
        thumbnail_size: Tuple of (width, height) for the thumbnail
        
    Returns:
        tuple: (image_filename, thumbnail_filename)
        
    Raises:
        ValueError: If the uploaded file is not a valid image
        OSError: If there's an error processing or saving the image
    """
    if not form_picture or not hasattr(form_picture, 'filename') or not form_picture.filename:
        raise ValueError("업로드할 파일이 없거나 잘못된 파일입니다.")
    
    filename = getattr(form_picture, 'filename', 'unknown')
    logger.info(f'이미지 처리 시작: {filename}')
    
    try:
        # 파일 포인터 위치 확인 및 초기화
        if hasattr(form_picture, 'seek'):
            form_picture.seek(0, 2)  # 파일 끝으로 이동
            file_size = form_picture.tell()
            form_picture.seek(0)  # 파일 포인터를 처음으로 되돌림
            logger.debug(f'파일 크기: {file_size} bytes')
        
        # 파일 확장자 추출
        file_ext = os.path.splitext(filename)[1].lower()
        if not file_ext:
            file_ext = '.jpg'  # 기본 확장자
        
        # 안전한 파일명 생성
        random_hex = secrets.token_hex(8)
        image_filename = f"{random_hex}{file_ext}"
        thumbnail_filename = f"{random_hex}_thumb{file_ext}"
        
        # 디렉토리 설정
        base_dir = Path(current_app.root_path) / 'static'
        uploads_dir = base_dir / 'uploads'
        thumbnails_dir = uploads_dir / 'thumbnails'
        
        # 디렉토리 생성
        try:
            uploads_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            thumbnails_dir.mkdir(exist_ok=True, mode=0o755)
        except OSError as e:
            logger.error(f'업로드 디렉토리 생성 실패: {str(e)}')
            raise OSError('파일을 저장할 디렉토리를 생성할 수 없습니다.')
        
        image_path = uploads_dir / image_filename
        thumbnail_path = thumbnails_dir / thumbnail_filename
        
        logger.debug(f'이미지 처리 중: {filename} -> {image_path}')
        
        # 이미지 처리
        try:
            # 이미지 열기 (파일 포인터가 올바르게 위치하도록 함)
            if hasattr(form_picture, 'seek'):
                form_picture.seek(0)
                
            with Image.open(form_picture) as img:
                # 메인 이미지 처리 및 저장
                main_img = process_image(img, output_size)
                main_img.save(
                    image_path,
                    quality=85,
                    optimize=True,
                    progressive=True,
                    format=img.format or 'JPEG'
                )
                
                # 썸네일 처리 및 저장
                thumb_img = process_image(img, thumbnail_size)
                thumb_img.save(
                    thumbnail_path,
                    quality=80,
                    optimize=True,
                    format=img.format or 'JPEG'
                )
                
                logger.info(f'이미지 저장 완료: {image_filename}, 썸네일: {thumbnail_filename}')
                
                # 메모리 해제
                main_img.close()
                thumb_img.close()
                
                return image_filename, thumbnail_filename
                
        except Exception as e:
            # 오류 발생 시 임시 파일 정리
            logger.error(f'이미지 처리 중 오류: {str(e)}', exc_info=True)
            for path in [image_path, thumbnail_path]:
                if path and path.exists():
                    try:
                        path.unlink()
                        logger.debug(f'임시 파일 삭제: {path}')
                    except OSError as e:
                        logger.error(f'파일 삭제 실패: {path}, 오류: {str(e)}')
            
            # 오류 메시지 구체화
            if 'truncated' in str(e).lower():
                raise ValueError('손상된 이미지 파일입니다. 다른 이미지로 시도해 주세요.')
            elif 'cannot identify' in str(e).lower():
                raise ValueError('지원하지 않는 이미지 형식입니다.')
            else:
                raise ValueError(f'이미지 처리 중 오류가 발생했습니다: {str(e)}')
                
    except Exception as e:
        logger.error(f'이미지 저장 중 치명적 오류: {str(e)}', exc_info=True)
        if isinstance(e, ValueError):
            raise e
        raise ValueError('파일을 처리하는 중 오류가 발생했습니다. 나중에 다시 시도해 주세요.')

def delete_cover_image(image_filename=None, thumbnail_filename=None):
    """
    Delete the cover image and its thumbnail if they exist.
    
    Args:
        image_filename (str, optional): The filename of the main image to delete
        thumbnail_filename (str, optional): The filename of the thumbnail to delete.
                                          If None, will be derived from image_filename.
    
    Returns:
        dict: {
            'success': bool,
            'deleted_files': list,
            'message': str,
            'error': str (optional)
        }
    """
    deleted_files = []
    
    if not image_filename and not thumbnail_filename:
        logger.warning('No filenames provided for deletion')
        return {
            'success': False,
            'deleted_files': [],
            'message': 'No files were deleted. No filenames provided.'
        }
    
    try:
        # Delete main image if provided
        if image_filename:
            try:
                image_path = Path(current_app.root_path) / 'static' / 'uploads' / image_filename
                if image_path.is_file():
                    logger.info(f'Deleting image: {image_path}')
                    image_path.unlink()
                    deleted_files.append(str(image_path))
                    logger.debug(f'Successfully deleted image: {image_path}')
                else:
                    logger.warning(f'Image file not found: {image_path}')
            except Exception as img_error:
                logger.error(f'Error deleting image {image_path}: {str(img_error)}', exc_info=True)
                # Continue to try deleting thumbnail even if image deletion fails
        
        # Delete thumbnail if provided or can be derived from image_filename
        thumb_to_delete = thumbnail_filename
        if not thumb_to_delete and image_filename:
            # Generate thumbnail filename from image filename
            name = Path(image_filename).stem
            ext = Path(image_filename).suffix
            thumb_to_delete = f"{name}_thumb{ext}"
        
        if thumb_to_delete:
            try:
                thumb_path = Path(current_app.root_path) / 'static' / 'uploads' / 'thumbnails' / thumb_to_delete
                if thumb_path.is_file():
                    logger.info(f'Deleting thumbnail: {thumb_path}')
                    thumb_path.unlink()
                    deleted_files.append(str(thumb_path))
                    logger.debug(f'Successfully deleted thumbnail: {thumb_path}')
                else:
                    logger.warning(f'Thumbnail file not found: {thumb_path}')
            except Exception as thumb_error:
                logger.error(f'Error deleting thumbnail {thumb_path}: {str(thumb_error)}', exc_info=True)
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'message': f'Successfully deleted {len(deleted_files)} file(s)'
        }
        
    except Exception as e:
        error_msg = f'Error deleting image files: {str(e)}'
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'deleted_files': deleted_files,
            'error': str(e),
            'message': f'Partial deletion completed. {len(deleted_files)} file(s) were deleted before error occurred.'
        }
