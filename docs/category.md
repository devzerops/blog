# 카테고리 시스템 문서

## 1. 모델 구조
```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy='dynamic')
```

## 2. 라우트 상세 로직

### `POST /admin/categories/new` (카테고리 생성)
1. **인증 확인**: `@admin_required` 데코레이터 적용
2. **폼 생성**: `CategoryForm` 인스턴스 생성
3. **폼 검증**:
   ```python
   if form.validate_on_submit():
       category = Category(name=form.name.data)
       db.session.add(category)
       db.session.commit()
   ```
4. **성공 시**: 플래시 메시지 출력 후 목록으로 리다이렉트
5. **실패 시**: 오류 메시지와 함께 폼 재표시

### `POST /admin/categories/edit/<id>` (카테고리 수정)
1. **인증 확인**: `@admin_required` 데코레이터 적용
2. **카테고리 조회**:
   ```python
   category = Category.query.get_or_404(id)
   ```
3. **폼 생성**: `CategoryForm` 인스턴스 (기존 데이터로 초기화)
4. **폼 검증**:
   ```python
   if form.validate_on_submit():
       category.name = form.name.data
       db.session.commit()
   ```
5. **성공 시**: 플래시 메시지 출력 후 목록으로 리다이렉트
6. **실패 시**: 오류 메시지와 함께 폼 재표시

## 3. 주요 기능
- 게시물 작성/수정 시 카테고리 선택
- 관리자 대시보드에서 카테고리 필터링
- 공개 게시물 목록에 카테고리 표시

## 4. 사용 템플릿
- `admin_categories_list.html`
- `admin_category_form.html`

## 🔴 주의: 현재 카테고리 연동 문제

### 백엔드 문제점
1. `Category.posts` 관계는 정의되었으나 `Post.category` 관계가 누락됨
2. `db.relationship()` 양방향 설정 불완전

### 프론트엔드 문제점
1. 카테고리 선택 폼이 제출되지 않음
2. AJAX 요청 시 `category_id` 파라미터 누락

### 해결 방안
```python
# Post 모델 수정
class Post(db.Model):
    category_id = db.Column(Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='posts')  # 추가
