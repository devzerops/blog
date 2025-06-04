
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from app.models import User
from app.auth import create_jwt_token
from app.database import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import jwt

bp_auth = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('사용자 아이디', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """관리자 로그인"""
    if 'admin_token' in session:
        try:
            jwt.decode(session['admin_token'], current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return redirect(url_for('admin.dashboard'))
        except jwt.InvalidTokenError:
            session.pop('admin_token', None)
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            token = create_jwt_token(user.id)
            session['admin_token'] = token
            flash('로그인 성공!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.', 'error')
    
    return render_template('public/login.html', form=form)

@bp_auth.route('/logout')
def logout():
    """로그아웃"""
    session.pop('admin_token', None)
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('public.index'))
