"""
Route package initialization.
This package contains all routes for the blog application.
"""

# Import all route modules here to make them available to the application
from app.routes.admin import bp_admin
# Import other blueprint modules when migrated
# from app.routes.public import bp_public
# from app.routes.auth import bp_auth

__all__ = ['bp_admin']  # Add other blueprints when migrated
