# 게시물 편집 시스템 문서

## 1. 주요 기능
- **CKEditor 5** 통합 (Super Build)
- **이미지 업로드**: 커스텀 업로드 어댑터 구현
- **마크다운 지원**: Marked.js로 변환
- **코드 하이라이팅**: highlight.js 적용
- **Mermaid 다이어그램** 지원

## 2. URL별 동작 로직

### `POST /admin/post/new` (게시물 생성)
1. **인증 확인**: `@admin_required` 데코레이터로 관리자 권한 검증
2. **폼 생성**: `PostForm` 인스턴스 생성
3. **카테고리 로드**: DB에서 모든 카테고리 조회하여 선택 옵션 설정
4. **폼 검증**:
   - 실패 시: 오류 메시지와 함께 편집 화면 재표시
   - 성공 시:
     1. 이미지 처리: `save_cover_image()`로 업로드
     2. 게시 상태 결정: 'publish' 버튼 클릭 여부 확인
     3. DB 저장: 새 `Post` 객체 생성 후 저장
5. **리다이렉트**: 성공 시 관리자 대시보드로 이동

### `POST /admin/post/edit/6` (게시물 수정)
1. **인증 확인**: `@admin_required` 데코레이터 적용
2. **게시물 조회**: ID=6인 게시물 존재 확인
3. **폼 생성**: `PostForm` 인스턴스 생성 (기존 데이터로 초기화)
4. **카테고리 로드**: DB에서 모든 카테고리 조회
5. **폼 검증**:
   - 실패 시: 오류 메시지와 함께 편집 화면 재표시
   - 성공 시:
     1. 이미지 처리: 새 이미지가 업로드된 경우 기존 파일 삭제 후 저장
     2. 게시 상태 업데이트: 발행/미발행 상태 변경
     3. DB 업데이트: 변경된 필드 저장
6. **리다이렉트**: 성공 시 관리자 대시보드로 이동

## 3. 편집 필드
```python
# Post 모델에서 편집 가능한 필드
title = db.Column(db.String(200))
content = db.Column(db.Text)
image_filename = db.Column(String(255))
alt_text = db.Column(String(200))
video_embed_url = db.Column(String(300))
tags = db.Column(String(255))
category_id = db.Column(Integer, db.ForeignKey('category.id'))
```

## 4. 주요 템플릿 로직 (`edit_post.html`)
- **실시간 미리보기**: CKEditor ↔ Markdown 변환
- **자동 저장**: 30초 간격으로 localStorage에 저장
- **이미지 업로드**:
  ```javascript
  class MyUploadAdapter {
    upload() {
      // 인증 토큰과 함께 서버에 이미지 전송
    }
  }
  ```
- **보안**:
  - CSRF 토큰 필수
  - 모든 API 요청에 JWT 인증 헤더 포함

## 🔴 게시물-카테고리 연동 문제

### 1. 폼 클래스 문제
```python
class PostForm(FlaskForm):
    # 누락된 필드:
    # category_id = SelectField('Category', coerce=int)
```

### 2. 템플릿 렌더링 문제
```html
<!-- 카테고리 선택기가 비활성화된 경우 -->
<select disabled>
  <!-- 옵션들 -->
</select>
```

### 3. 데이터 바인딩 실패
- `form.category_id.data` 바인딩되지 않음
- 폼 제출 시 `request.form`에 `category_id` 없음
