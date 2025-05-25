from flask import request, current_app

def debug_form_data():
    """Log all form data for debugging purposes"""
    current_app.logger.info("===== FORM DATA DEBUG =====")
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Content type: {request.content_type}")
    
    # Log all form fields
    if request.form:
        current_app.logger.info("Form data:")
        for key, value in request.form.items():
            current_app.logger.info(f"  {key}: {value[:100] if isinstance(value, str) and len(value) > 100 else value}")
    else:
        current_app.logger.info("No form data found")
    
    # Log all files
    if request.files:
        current_app.logger.info("Files:")
        for key, file in request.files.items():
            if file.filename:
                current_app.logger.info(f"  {key}: {file.filename} ({file.content_type})")
    else:
        current_app.logger.info("No files found")
    
    current_app.logger.info("===== END FORM DATA DEBUG =====")
