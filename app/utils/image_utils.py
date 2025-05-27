import os
from PIL import Image
from io import BytesIO
import secrets
from flask import current_app

def save_cover_image(form_picture, output_size=(1200, 630), thumbnail_size=(300, 200)):
    """
    Save the uploaded cover image and generate a thumbnail.
    Returns a tuple of (image_filename, thumbnail_filename)
    """
    # Generate a random filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    image_filename = random_hex + f_ext
    thumbnail_filename = f"{random_hex}_thumb{f_ext}"
    
    # Create paths
    image_path = os.path.join(current_app.root_path, 'static/uploads', image_filename)
    thumbnail_path = os.path.join(current_app.root_path, 'static/uploads/thumbnails', thumbnail_filename)
    
    # Create thumbnails directory if it doesn't exist
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    
    try:
        # Open the image
        current_app.logger.debug(f"Opening image file: {form_picture.filename}")
        img = Image.open(form_picture)
        current_app.logger.debug(f"Image format: {img.format}, size: {img.size}, mode: {img.mode}")
        
        # Create a copy of the image for the main image
        main_img = img.copy()
        
        # Resize the main image
        current_app.logger.debug(f"Resizing main image to max {output_size}")
        main_img.thumbnail(output_size, Image.Resampling.LANCZOS)
        
        # Save the main image
        current_app.logger.debug(f"Saving main image to {image_path}")
        main_img.save(image_path, quality=85, optimize=True)
        
        # Create a copy for the thumbnail
        thumb_img = img.copy()
        
        # Create and save thumbnail
        current_app.logger.debug(f"Creating thumbnail with size {thumbnail_size}")
        thumb_img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        current_app.logger.debug(f"Thumbnail size after resizing: {thumb_img.size}")
        
        # Ensure the thumbnails directory exists
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        current_app.logger.debug(f"Saving thumbnail to {thumbnail_path}")
        thumb_img.save(thumbnail_path, quality=85, optimize=True)
        
        # Verify the thumbnail was saved
        if os.path.exists(thumbnail_path):
            current_app.logger.debug(f"Thumbnail successfully saved to {thumbnail_path}")
        else:
            current_app.logger.error(f"Failed to save thumbnail to {thumbnail_path}")
        
        return image_filename, thumbnail_filename
        
    except Exception as e:
        current_app.logger.error(f"Error processing image: {e}")
        if os.path.exists(image_path):
            os.remove(image_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        raise

def delete_cover_image(image_filename, thumbnail_filename=None):
    """Delete the cover image and its thumbnail if they exist"""
    try:
        if image_filename:
            image_path = os.path.join(current_app.root_path, 'static/uploads', image_filename)
            if os.path.exists(image_path):
                current_app.logger.debug(f"Deleting image: {image_path}")
                os.remove(image_path)
                current_app.logger.debug(f"Successfully deleted image: {image_path}")
            else:
                current_app.logger.warning(f"Image file not found: {image_path}")
        
        if thumbnail_filename:
            thumb_path = os.path.join(current_app.root_path, 'static/uploads/thumbnails', thumbnail_filename)
            if os.path.exists(thumb_path):
                current_app.logger.debug(f"Deleting thumbnail: {thumb_path}")
                os.remove(thumb_path)
                current_app.logger.debug(f"Successfully deleted thumbnail: {thumb_path}")
            else:
                current_app.logger.warning(f"Thumbnail file not found: {thumb_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting image files: {e}", exc_info=True)
