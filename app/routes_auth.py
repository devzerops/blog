from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
# from werkzeug.security import check_password_hash # Not directly needed here, user.check_password handles it
from app.models import User
from app.auth import create_jwt_token
# from app.database import db # Not directly needed for db operations in this file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
import jwt # for decoding existing token

bp_auth = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

@bp_auth.route('/login', methods=['GET', 'POST'])
def login_page():
    # If user is already logged in and token is valid, redirect to dashboard
    if 'admin_token' in session:
        try:
            # Check if token is still valid (not expired, etc.)
            jwt.decode(session['admin_token'], current_app.config['SECRET_KEY'], algorithms=["HS256"])
            flash('이미 로그인되어 있습니다.', 'info')
            return redirect(url_for('admin.dashboard'))
        except jwt.ExpiredSignatureError:
            session.pop('admin_token', None) # Clear expired token
            flash('세션이 만료되었습니다. 다시 로그인해주세요.', 'warning')
        except jwt.InvalidTokenError:
            session.pop('admin_token', None) # Clear invalid token
            flash('잘못된 세션 정보입니다. 다시 로그인해주세요.', 'danger')
        # Fall through to login form if token was invalid/expired

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            token = create_jwt_token(user.id)
            session['admin_token'] = token
            session['username'] = user.username # Store username for display in templates
            flash('성공적으로 로그인되었습니다!', 'success')
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'): # Basic security check for open redirect
                return redirect(next_url)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.', 'danger')
    return render_template('public/login.html', title='관리자 로그인', form=form)

@bp_auth.route('/logout')
def logout():
    session.pop('admin_token', None)
    session.pop('username', None)
    flash('성공적으로 로그아웃되었습니다.', 'success')
    return redirect(url_for('auth.login_page'))
