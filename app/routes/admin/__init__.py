"""
Admin routes package initialization.
Contains all routes for the admin section of the blog.
"""

from flask import Blueprint

# Create admin blueprint
bp_admin = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes after blueprint creation to avoid circular imports
from app.routes.admin import dashboard
from app.routes.admin import posts
from app.routes.admin import categories
from app.routes.admin import media
from app.routes.admin import settings
from app.routes.admin import statistics
from app.routes.admin import backup

# Only export the blueprint
__all__ = ['bp_admin']
