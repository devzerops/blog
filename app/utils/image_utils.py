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
    Save the uploaded image and generate a thumbnail.
    
    Args:
        form_picture: FileStorage object from Flask
        output_size: Tuple (width, height) for the main image (not used, kept for backward compatibility)
        thumbnail_size: Tuple (width, height) for the thumbnail
        
    Returns:
        tuple: (None, thumbnail_filename) if successful, (None, None) otherwise
    """
    if not form_picture or not hasattr(form_picture, 'filename') or not form_picture.filename:
        logger.error("No file provided or invalid file object")
        return None, None
    
    try:
        # Validate the uploaded file
        filename, ext, mime_type = validate_image(form_picture)
        logger.info(f"이미지 처리 시작: {filename}")
        
        # Generate a random filename for the thumbnail
        random_hex = secrets.token_hex(8)
        thumbnail_filename = f"{random_hex}_thumb{ext}"
        
        # Create uploads directory if it doesn't exist (relative to app root)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create thumbnails directory if it doesn't exist
        thumbnail_folder = os.path.join(upload_folder, 'thumbnails')
        os.makedirs(thumbnail_folder, exist_ok=True)
        
        thumbnail_path = None
        try:
            with Image.open(form_picture) as img:
                # Process and save thumbnail only
                processed_thumb = process_image(img, thumbnail_size)
                thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)
                
                # Save thumbnail with optimized settings
                if img.format == 'PNG':
                    processed_thumb.save(thumbnail_path, format='PNG', optimize=True, quality=80)
                else:
                    processed_thumb.convert('RGB').save(
                        thumbnail_path,
                        format='JPEG',
                        quality=80,
                        optimize=True,
                        progressive=True
                    )
                
                logger.debug(f"Thumbnail saved: {thumbnail_path}")
                return None, thumbnail_filename
                
        except Exception as e:
            logger.error(f"이미지 처리 중 오류: {str(e)}", exc_info=True)
            # Delete thumbnail if it was created
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                except Exception as del_err:
                    logger.error(f'Failed to delete thumbnail: {del_err}')
            return None, None
            
    except Exception as e:
        logger.error(f"이미지 유효성 검사 실패: {str(e)}", exc_info=True)
        return None, None
    finally:
        # 파일 포인터 초기화 (재사용을 위해)
        if hasattr(form_picture, 'seek'):
            try:
                form_picture.seek(0)
            except Exception as e:
                logger.warning(f'파일 포인터 초기화 실패: {str(e)}')

def delete_cover_image(thumbnail_filename):
    """
    Delete the thumbnail image if it exists.
    
    Args:
        thumbnail_filename (str): The filename of the thumbnail to delete.
    
    Returns:
        dict: {
            'success': bool,
            'deleted_files': list,
            'message': str,
            'error': str (optional)
        }
    """
    deleted_files = []
    upload_folder = os.path.join(current_app.root_path, 'static/uploads/thumbnails')
    
    try:
        # Delete thumbnail if provided
        if thumbnail_filename:
            thumbnail_path = os.path.join(upload_folder, thumbnail_filename)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                deleted_files.append(f"thumbnails/{thumbnail_filename}")
                logger.info(f"Deleted thumbnail: {thumbnail_filename}")
        
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
