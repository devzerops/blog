"""
Admin site settings routes.
Contains routes for managing site settings and admin profile.
"""

from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.exceptions import NotFound

from app.database import db
from app.models import User, SiteSetting
from app.forms import SiteSettingsForm, SettingsForm
from app.auth import admin_required, token_required, get_current_user_if_logged_in
from app.routes.admin import bp_admin


@bp_admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def site_settings(current_user):
    """Site settings management"""
    # Get or create site settings
    site_settings = SiteSetting.query.first()
    if not site_settings:
        site_settings = SiteSetting()
        db.session.add(site_settings)
        db.session.commit()
    
    form = SiteSettingsForm(obj=site_settings)
    
    if form.validate_on_submit():
        form.populate_obj(site_settings)
        db.session.commit()
        flash('사이트 설정이 업데이트되었습니다.', 'success')
        return redirect(url_for('admin.site_settings'))
    
    return render_template('admin/settings.html', 
                          title='사이트 설정', 
                          form=form, 
                          current_user=current_user)


@bp_admin.route('/profile-settings', methods=['GET', 'POST'])
@token_required
def admin_profile_settings(current_user):
    """Admin profile settings"""
    # Get current user from token
    current_user_from_token = get_current_user_if_logged_in()
    if not current_user_from_token:
        flash('인증에 실패했습니다. 다시 로그인해주세요.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = SettingsForm(original_username=current_user_from_token.username, obj=current_user_from_token)
    
    if form.validate_on_submit():
        # Check if password change is requested
        if form.new_password.data:
            if not form.current_password.data:
                flash('새 비밀번호를 설정하려면 현재 비밀번호를 입력해야 합니다.', 'danger')
                return render_template('admin/admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)
            if not current_user_from_token.check_password(form.current_password.data):
                flash('현재 비밀번호가 정확하지 않습니다.', 'danger')
                return render_template('admin/admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)
            current_user_from_token.set_password(form.new_password.data)
            flash('비밀번호가 성공적으로 변경되었습니다.', 'info')
        
        # Update other user information
        current_user_from_token.username = form.username.data
        current_user_from_token.email = form.email.data
        current_user_from_token.display_name = form.display_name.data
        current_user_from_token.bio = form.bio.data
        
        db.session.commit()
        flash('프로필이 성공적으로 업데이트되었습니다.', 'success')
        return redirect(url_for('admin.admin_profile_settings'))
    
    # For GET request, populate form fields that are not directly mapped by obj if necessary
    # Example: form.username.data = current_user_from_token.username (already handled by obj)

    return render_template('admin/admin_profile_settings.html', title='관리자 프로필 설정', form=form, current_user=current_user_from_token)
