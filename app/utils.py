# This file can be used for utility functions if needed.
# For example, more complex file handling, text processing, etc.

import os
import uuid # Not strictly needed if using timestamp for uniqueness
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime, timezone

def save_uploaded_image(form_image_file):
    """Saves an image uploaded via a form to the UPLOAD_FOLDER, ensuring a unique name."""
    if not form_image_file or not form_image_file.filename:
        return None
    
    original_filename = secure_filename(form_image_file.filename)
    # Create a unique filename using timestamp and original name part
    # This helps avoid collisions and keeps some context of the original file name.
    timestamp_prefix = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    unique_filename = f"{timestamp_prefix}_{original_filename}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    image_path = os.path.join(upload_folder, unique_filename)
    
    try:
        # Ensure upload folder exists (though __init__ should handle it)
        os.makedirs(upload_folder, exist_ok=True) 
        form_image_file.save(image_path)
        return unique_filename
    except Exception as e:
        current_app.logger.error(f"Failed to save image {unique_filename} to {image_path}: {e}")
        return None

def delete_uploaded_image(filename):
    """Deletes an image from the UPLOAD_FOLDER."""
    if not filename:
        return False
    
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            current_app.logger.info(f"Successfully deleted image: {filename}")
            return True
        else:
            current_app.logger.warning(f"Attempted to delete non-existent image: {filename}")
            return False
    except Exception as e:
        current_app.logger.error(f"Failed to delete image {filename}: {e}")
    return False

# Example of how it might be used in a route (conceptual):
# from flask import request, flash
# from .utils import save_uploaded_image, delete_uploaded_image
# ...
# if form.image_field.data:
#     old_image = post.image_filename
#     new_image_filename = save_uploaded_image(form.image_field.data)
#     if new_image_filename:
#         if old_image:
#             delete_uploaded_image(old_image)
#         post.image_filename = new_image_filename
#     else:
#         flash('Image upload failed.', 'danger')

