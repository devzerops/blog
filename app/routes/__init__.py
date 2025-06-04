"""
Route package initialization.
This package contains all routes for the blog application.
"""

from app.routes.public import bp_public
from app.routes.auth import bp_auth
from app.routes.admin import bp_admin

__all__ = ['bp_public', 'bp_auth', 'bp_admin']