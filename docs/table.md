# 데이터베이스 테이블 문서

## 🔴 카테고리 연동 문제 분석

### 1. 모델 간 관계 문제
```python
# 문제점: Post 모델에 category_id는 있지만 관계 설정이 누락됨
class Post(db.Model):
    category_id = db.Column(Integer, db.ForeignKey('category.id'))
    # 누락된 부분:
    # category = db.relationship('Category', back_populates='posts')
```

### 2. 폼 처리 오류
- `PostForm`에서 `category` 필드가 `QuerySelectField`로 정의되지 않음
- `category_id`가 폼 데이터로 전달되지 않는 문제

### 3. 템플릿 문제 (`edit_post.html`)
```html
<!-- 문제 1: select name이 'category_id'가 아닌 경우 -->
<select name="category">  <!-- 잘못됨 -->
<select name="category_id">  <!-- 올바름 -->

<!-- 문제 2: 옵션 value가 카테고리 ID가 아닌 경우 -->
<option value="{{ category.name }}">  <!-- 잘못됨 -->
<option value="{{ category.id }}">  <!-- 올바름 -->
```

### 4. 라우트 처리 누락
```python
# 게시물 저장 시 카테고리 ID 할당 누락
@admin.route('/post/new', methods=['POST'])
def new_post():
    if form.validate_on_submit():
        post = Post()
        # 누락된 부분:
        # post.category_id = form.category_id.data
```

## 🛠️ 수정 권장 사항
1. 모델 관계 명시적 설정
2. `PostForm`에 `QuerySelectField` 추가
3. 템플릿에서 `name` 및 `value` 속성 검증
4. 라우트에서 카테고리 ID 명시적 할당

## 📌 기존 테이블 구조 (이하 내용 유지)

## 📌 User 테이블
- **설명**: 관리자 사용자 정보
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 설명 |
  |--------|------|------|----------|------|
  | id | Integer | - | NO | PK |
  | username | String | 64 | NO | 유니크한 사용자명 |
  | password_hash | String | 256 | NO | 암호화된 비밀번호 |

## 📌 Category 테이블
- **설명**: 게시물 카테고리
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 설명 |
  |--------|------|------|----------|------|
  | id | Integer | - | NO | PK |
  | name | String | 100 | NO | 유니크한 카테고리명 |

## 📌 Post 테이블
- **설명**: 블로그 게시물
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 설명 |
  |--------|------|------|----------|------|
  | id | Integer | - | NO | PK |
  | title | String | 200 | NO | 게시물 제목 |
  | content | Text | - | NO | 게시물 내용 (HTML) |
  | created_at | DateTime | - | NO | 생성일시 |
  | user_id | Integer | - | NO | 작성자 FK |
  | image_filename | String | 255 | YES | 커버 이미지 파일명 |
  | thumbnail_filename | String | 255 | YES | 썸네일 파일명 |
  | alt_text | String | 200 | YES | 이미지 대체 텍스트 |
  | video_embed_url | String | 300 | YES | 비디오 임베드 URL |
  | meta_description | String | 300 | YES | SEO 메타 설명 |
  | is_published | Boolean | - | NO | 발행 여부 |
  | published_at | DateTime | - | YES | 발행일시 |
  | views | Integer | - | YES | 조회수 |
  | updated_at | DateTime | - | YES | 수정일시 |
  | tags | String | 255 | YES | 태그 (쉼표 구분) |
  | category_id | Integer | - | YES | 카테고리 FK |

## 📌 Comment 테이블
- **설명**: 게시물 댓글
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 설명 |
  |--------|------|------|----------|------|
  | id | Integer | - | NO | PK |
  | nickname | String | 100 | NO | 작성자 닉네임 |
  | content | Text | - | NO | 댓글 내용 |
  | created_at | DateTime | - | NO | 작성일시 |
  | post_id | Integer | - | NO | 게시물 FK |
  | ip_address | String | 45 | YES | 작성자 IP |
  | parent_id | Integer | - | YES | 부모 댓글 FK (중첩 댓글용) |

## 📌 PageView 테이블
- **설명**: 페이지 뷰 로그
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 설명 |
  |--------|------|------|----------|------|
  | id | Integer | - | NO | PK |
  | path | String | 255 | NO | 접속 경로 |
  | ip_address | String | 45 | YES | 접속자 IP |
  | user_agent | String | 255 | YES | 사용자 에이전트 |
  | timestamp | DateTime | - | NO | 접속시간 |
  | post_id | Integer | - | YES | 게시물 FK (게시물 페이지인 경우) |

## 📌 SiteSetting 테이블
- **설명**: 사이트 설정
- **필드**:
  | 필드명 | 타입 | 길이 | Nullable | 기본값 | 설명 |
  |--------|------|------|----------|--------|------|
  | id | Integer | - | NO | - | PK |
  | site_title | String | 100 | YES | "My Blog" | 사이트 제목 |
  | site_description | Text | - | YES | - | 사이트 설명 |
  | site_domain | String | 255 | YES | - | 사이트 도메인 |
  | favicon_filename | String | 255 | YES | - | 파비콘 파일명 |
  | posts_per_page | Integer | - | YES | 10 | 페이지당 게시물 수 |
  | admin_email | String | 120 | YES | - | 관리자 이메일 |
  | admin_github_url | String | 255 | YES | - | 관리자 GitHub URL |
  | ad_sense_code | Text | - | YES | - | 애드센스 코드 |
  | google_analytics_id | String | 50 | YES | - | GA 추적 ID |
  | footer_copyright_text | String | 255 | YES | "{year} {site_title}. All rights reserved." | 푸터 저작권 텍스트 |
  | about_content | Text | - | YES | - | About 페이지 내용 |

## 🔍 불필요할 수 있는 필드
1. `Post.video_embed_url` - 비디오 기능 미사용 시
2. `Post.meta_description` - SEO 자동생성 가능 시
3. `Comment.parent_id` - 중첩 댓글 미사용 시
4. `PageView.user_agent` - 상세 분석 미진행 시
5. `SiteSetting.ad_sense_code` - 광고 미사용 시
