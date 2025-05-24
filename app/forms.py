from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, FileField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, URL
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('사용자 아이디', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    username = StringField('사용자 아이디', validators=[DataRequired(), Length(min=3, max=64)])
    # Removed email field for simplicity as per user's existing User model
    # email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    password2 = PasswordField(
        '비밀번호 확인', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('가입')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('이미 사용 중인 사용자 아이디입니다.')

    # Removed email validation as email field is removed
    # def validate_email(self, email):
    #     user = User.query.filter_by(email=email.data).first()
    #     if user is not None:
    #         raise ValidationError('Please use a different email address.')

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('내용', validators=[DataRequired()])
    image = FileField('커버 이미지 (선택 사항)')
    alt_text = StringField('이미지 설명 (Alt Text)', validators=[Length(max=200)]) 
    video_embed_url = StringField('동영상 URL (선택 사항)', validators=[Optional(), URL(), Length(max=300)]) 
    tags = StringField('태그 (쉼표로 구분)', validators=[Optional(), Length(max=255)]) 
    meta_description = TextAreaField('메타 설명 (SEO, 선택 사항)', validators=[Optional(), Length(max=300)]) 
    is_published = BooleanField('공개 발행', default=True)
    submit = SubmitField('저장')

class SettingsForm(FlaskForm):
    username = StringField('사용자 아이디', validators=[DataRequired(), Length(min=3, max=64)])
    # email = StringField('이메일', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('현재 비밀번호')
    new_password = PasswordField('새 비밀번호')
    confirm_new_password = PasswordField('새 비밀번호 확인', validators=[EqualTo('new_password', message='새 비밀번호가 일치하지 않습니다.')])
    submit = SubmitField('변경 사항 저장')

    def __init__(self, original_username, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        # self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('이미 사용 중인 사용자 아이디입니다. 다른 아이디를 입력해주세요.')

    # def validate_email(self, email):
    #     if email.data != self.original_email:
    #         user = User.query.filter_by(email=self.email.data).first()
    #         if user:
    #             raise ValidationError('That email is taken. Please choose a different one.')

class CommentForm(FlaskForm):
    nickname = StringField('닉네임', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('댓글 내용', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('댓글 달기')

class DeleteForm(FlaskForm):
    submit = SubmitField('삭제') # This field might not be strictly necessary if button is styled in template

class ImportForm(FlaskForm):
    backup_file = FileField('백업 파일 (ZIP)', validators=[DataRequired()])
    submit = SubmitField('콘텐츠 복원 시작')
