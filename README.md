# DevZero 블로그 플랫폼

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)

Flask 기반의 고성능 블로그 플랫폼으로, 개발자들을 위한 기술 블로그 운영에 최적화되어 있습니다. 모던한 UI/UX와 강력한 관리자 기능을 제공합니다.

## 🚀 주요 기능

### 📝 게시물 관리
- **WYSIWYG 에디터** - CKEditor 5 기반의 풍부한 텍스트 편집 기능
- **마크다운 지원** - GitHub 스타일 마크다운 에디터 통합
- **자동 저장** - 작성 중인 글 자동 저장 기능
- **버전 관리** - 게시물 수정 이력 추적 및 복원
- **일괄 작업** - 여러 게시물에 대한 일괄 공개/비공개 설정
- **고급 검색** - 제목, 내용, 태그, 카테고리 통합 검색
- **이미지 최적화** - 업로드 시 자동 리사이징 및 WebP 변환
- **OG 태그 자동 생성** - SNS 공유 최적화

### 💬 댓글 시스템
- **계층형 댓글** - 무한 대댓글 지원
- **마크다운 지원** - 코드 하이라이팅 포함
- **실시간 알림** - 댓글 등록 시 관리자 알림
- **스팸 방지** - reCAPTCHA 통합
- **소셜 로그인** - 구글, 깃허브 연동 (옵션)

### 🔐 사용자 인증 및 권한
- **JWT 기반 인증** - 안전한 토큰 기반 인증
- **역할 기반 접근 제어** - 관리자, 에디터, 구독자 등
- **이중 인증** - OTP 지원
- **로그인 시도 제한** - Brute Force 공격 방지
- **세션 관리** - 다중 기기에서의 세션 추적

### ⚙️ 사이트 관리
- **통계 대시보드** - 방문자, 인기 게시물, 트래픽 분석
- **백업 및 복구** - 전체 사이트 백업/복원 기능
- **이미지 라이브러리** - 미디어 파일 관리
- **사용자 정의 CSS/JS** - 테마 수정 없이 스타일/스크립트 추가
- **API 문서** - Swagger UI 통합
- **검색 엔진 최적화** - 사이트맵, robots.txt 자동 생성
- **구글 애널리틱스 4** - 실시간 분석 통합
- **에러 로깅** - Sentry 연동

### 🎨 테마 시스템
- **다크/라이트 모드** - 사용자 선택 가능
- **반응형 디자인** - 모바일 최적화
- **커스텀 위젯** - 사이드바 위젯 관리
- **코드 하이라이팅** - 100+ 프로그래밍 언어 지원
- **다이어그램** - Mermaid.js 통합

## 🏗 시스템 아키텍처

```mermaid
graph TD
    A[사용자] -->|요청| B[Nginx]
    B -->|정적 파일| C[Static Files]
    B -->|동적 요청| D[Gunicorn]
    D --> E[Flask App]
    E --> F[PostgreSQL]
    E --> G[Redis]
    H[관리자] -->|관리| E
    I[백업 서버] -->|동기화| J[클라우드 스토리지]
```

### 컴포넌트 설명
- **Nginx**: 정적 파일 서빙 및 리버스 프록시
- **Gunicorn**: WSGI HTTP 서버
- **Flask**: 웹 애플리케이션 프레임워크
- **PostgreSQL**: 주 데이터베이스
- **Redis**: 캐싱 및 세션 저장소
- **Celery**: 비동기 작업 처리
- **Docker**: 컨테이너화 및 배포

## 🛠 기술 스택

### 백엔드
- Python 3.8+
- Flask 2.0+
- SQLAlchemy
- PostgreSQL / SQLite
- Gunicorn (프로덕션 서버)

### 프론트엔드
- HTML5 / CSS3
- JavaScript (Vanilla)
- Bootstrap 5
- TinyMCE 에디터

### 데이터베이스
- PostgreSQL (프로덕션)
- SQLite (개발)
- Flask-Migrate (데이터베이스 마이그레이션)

### 배포
- Docker
- Docker Compose
- Nginx (리버스 프록시)

## 🚀 시작하기

### 사전 요구사항
- Python 3.8 이상
- PostgreSQL (또는 SQLite)
- Docker 및 Docker Compose (선택사항)

### 설치

1. 저장소 클론
   ```bash
   git clone https://github.com/devzerops/blog.git
   cd blog
   ```

2. 가상환경 설정 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   .\venv\Scripts\activate  # Windows
   ```

3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정
   ```bash
   cp .env.example .env
   # .env 파일을 열어 필요한 설정 수정
   ```

5. 데이터베이스 초기화
   ```bash
   flask db upgrade
   flask init-db
   ```

### Docker를 사용한 실행

```bash
docker-compose up --build
```

### 개발 서버 실행

```bash
flask run
```

## 🗄 데이터베이스 스키마

### ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    USER ||--o{ POST : "작성"
    USER ||--o{ COMMENT : "작성"
    USER ||--o{ USER_ROLE : "소유"
    
    POST ||--o{ COMMENT : "댓글"
    POST ||--o{ POST_TAG : "태그"
    POST ||--o{ POST_CATEGORY : "분류"
    POST ||--o{ POST_VIEW : "조회"
    POST ||--o{ POST_META : "메타데이터"
    
    CATEGORY ||--o{ POST_CATEGORY : "포함"
    TAG ||--o{ POST_TAG : "연결"
    
    COMMENT ||--o{ COMMENT : "대댓글"
    
    ROLE ||--o{ USER_ROLE : "할당"
    ROLE ||--o{ PERMISSION : "권한"
    
    entity "USER" as user {
        *id integer "PK"
        username string "인덱스"
        email string "유니크"
        password_hash string
        avatar string
        bio text
        is_active boolean
        created_at datetime
        updated_at datetime
        last_login_at datetime
    }
    
    entity "POST" as post {
        *id integer "PK"
        title string
        slug string "유니크 인덱스"
        content text
        excerpt text
        status enum('draft','published','archived')
        comment_status boolean
        comment_count integer
        view_count integer
        user_id integer "FK"
        created_at datetime
        updated_at datetime
        published_at datetime
    }
    
    entity "COMMENT" as comment {
        *id integer "PK"
        content text
        author string
        email string
        ip_address string
        status enum('pending','approved','spam','trash')
        parent_id integer "Self-reference FK"
        post_id integer "FK"
        user_id integer "FK (Nullable)"
        created_at datetime
        updated_at datetime
    }
```

### 주요 테이블 설명

#### 1. 사용자 관리
- **users**: 사용자 계정 정보 저장
- **roles**: 역할 정의 (관리자, 에디터, 구독자 등)
- **user_roles**: 사용자-역할 매핑
- **permissions**: 세부 권한 정의

#### 2. 콘텐츠 관리
- **posts**: 게시물 메타데이터 및 내용
- **post_meta**: 게시물 추가 메타데이터 (SEO, 사용자 정의 필드 등)
- **categories**: 카테고리 분류
- **tags**: 태그 관리
- **post_categories**: 게시물-카테고리 다대다 관계
- **post_tags**: 게시물-태그 다대다 관계

#### 3. 상호작용
- **comments**: 댓글 및 대댓글
- **post_views**: 조회수 추적
- **likes**: 좋아요 기능
- **bookmarks**: 북마크 기능

#### 4. 시스템
- **settings**: 사이트 설정
- **activity_logs**: 활동 로그
- **sessions**: 사용자 세션 관리
- **migrations**: 데이터베이스 마이그레이션 이력

### 인덱스 전략
- 자주 조회되는 필드에 대한 인덱스 적용
- 외래키 제약조건에 자동 생성되는 인덱스 활용
- 복합 인덱스로 쿼리 성능 최적화
- Full-text 검색을 위한 인덱스 설정

## ⚙️ 환경 변수 설정

`.env` 파일을 생성하여 다음 변수들을 설정하세요:

```env
# 애플리케이션 설정
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@localhost:5432/blog_db
DATABASE_TEST_URL=sqlite:///test.db

# 이메일 설정
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Redis 설정 (캐싱 및 작업 큐용)
REDIS_URL=redis://localhost:6379/0

# 파일 업로드 설정
UPLOAD_FOLDER=/path/to/upload/folder
MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'}

# 구글 리캡차 설정
RECAPTCHA_PUBLIC_KEY=your-recaptcha-site-key
RECAPTCHA_PRIVATE_KEY=your-recaptcha-secret-key

# 소셜 로그인 설정
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# 모니터링 및 분석
SENTRY_DSN=your-sentry-dsn
GOOGLE_ANALYTICS_ID=UA-XXXXX-Y
```

## 🚀 배포 가이드

### Docker를 사용한 배포

1. Docker 및 Docker Compose 설치
2. `.env` 파일 설정
3. 다음 명령어로 서비스 시작:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 수동 배포 (Ubuntu 서버 기준)

1. 시스템 패키지 업데이트 및 의존성 설치:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx supervisor
```

2. 애플리케이션 설정:
```bash
# 프로젝트 클론
git clone https://github.com/devzerops/blog.git /opt/blog
cd /opt/blog

# 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
nano .env  # 환경변수 수정

# 데이터베이스 마이그레이션
flask db upgrade
flask init-db
```

3. Gunicorn 설정:
```bash
# gunicorn.service 파일 생성
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn instance to serve blog
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/blog
Environment="PATH=/opt/blog/venv/bin"
ExecStart=/opt/blog/venv/bin/gunicorn --workers 3 --bind unix:blog.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
```

4. Nginx 설정:
```bash
sudo nano /etc/nginx/sites-available/blog
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/blog/blog.sock;
    }

    location /static {
        alias /opt/blog/app/static;
        expires 30d;
    }

    location /uploads {
        alias /path/to/upload/folder;
        expires 30d;
    }
}
```

5. 서비스 활성화 및 시작:
```bash
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## 🔧 개발 가이드

### 개발 서버 실행

```bash
# 개발 모드로 실행
flask run --debug

# 특정 포트로 실행 (예: 5001)
flask run --port 5001
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 모듈 실행
pytest tests/test_auth.py

# 코드 커버리지 보고서 생성
pytest --cov=app tests/
```

### 마이그레이션

```bash
# 마이그레이션 생성
flask db migrate -m "설명"

# 마이그레이션 적용
flask db upgrade

# 특정 버전으로 되돌리기
flask db downgrade <revision>
```

## 📝 API 문서

API 문서는 Swagger UI를 통해 `/api/docs`에서 확인할 수 있습니다.

### 인증

#### 관리자 로그인
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

#### 토큰 갱신
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### 게시물

#### 게시물 목록 조회
```http
GET /api/posts?page=1&per_page=10&category=tech&q=search+term
```

#### 게시물 생성
```http
POST /api/posts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "새로운 게시물",
  "content": "게시물 내용...",
  "category_id": 1,
  "tags": ["태그1", "태그2"],
  "status": "draft"
}
```

## 🧪 테스트

### 테스트 환경 설정

1. 테스트용 데이터베이스 생성 (SQLite 사용 시):
```bash
sqlite3 instance/test.db < tests/schema.sql
```

2. 테스트 실행:
```bash
# 모든 테스트 실행
pytest

# 코드 커버리지 포함
pytest --cov=app --cov-report=term-missing

# 테스트 속도 향상을 위해 병렬 실행
pytest -n auto
```

### 테스트 커버리지

```bash
# 커버리지 보고서 생성
pytest --cov=app --cov-report=html

# 터미널에 간단한 보고서 표시
pytest --cov=app --cov-report=term-missing
```

## 🛠 문제 해결

### 일반적인 문제

1. **데이터베이스 연결 오류**
   - `.env` 파일의 `DATABASE_URL`이 올바른지 확인하세요.
   - PostgreSQL 서버가 실행 중인지 확인하세요.

2. **이미지 업로드 실패**
   - 업로드 폴더가 존재하고 쓰기 권한이 있는지 확인하세요.
   - `MAX_CONTENT_LENGTH` 제한을 초과하지 않았는지 확인하세요.

3. **이메일 발송 실패**
   - 이메일 서버 설정이 올바른지 확인하세요.
   - 스팸 폴더를 확인하세요.

### 로그 확인

```bash
# 애플리케이션 로그
journalctl -u gunicorn -f

# Nginx 에러 로그
tail -f /var/log/nginx/error.log

# 애플리케이션 디버그 모드
DEBUG=1 flask run
```

## 📄 라이센스

이 프로젝트는 [MIT 라이센스](LICENSE) 하에 배포됩니다.

## 👥 기여 가이드라인

기여를 환영합니다! 기여를 원하시면 다음 단계를 따라주세요:

1. 이슈를 생성하여 변경사항을 논의하세요.
2. 포크하여 기능 브랜치를 만드세요:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. 변경사항을 커밋하세요:
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. 브랜치에 푸시하세요:
   ```bash
   git push origin feature/amazing-feature
   ```
5. 풀 리퀘스트를 오픈하세요.

### 코드 스타일 가이드

- PEP 8 스타일 가이드를 따릅니다.
- 모든 새로운 Python 파일은 docstring을 포함해야 합니다.
- 테스트 커버리지를 80% 이상 유지하세요.
- 새로운 기능에는 반드시 테스트를 작성하세요.

## 📞 연락처

프로젝트 팀 - [@devzerops](https://github.com/devzerops)

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트를 기반으로 합니다:

- [Flask](https://flask.palletsprojects.com/) - 웹 프레임워크
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Bootstrap 5](https://getbootstrap.com/) - 프론트엔드 프레임워크
- [CKEditor 5](https://ckeditor.com/ckeditor-5/) - 리치 텍스트 에디터
- [Font Awesome](https://fontawesome.com/) - 아이콘 라이브러리
- [Mermaid.js](https://mermaid-js.github.io/) - 다이어그램 생성

## 📊 프로젝트 상태

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/devzerops/blog/graphs/commit-activity)
[![GitHub issues](https://img.shields.io/github/issues/devzerops/blog)](https://github.com/devzerops/blog/issues)
[![GitHub stars](https://img.shields.io/github/stars/devzerops/blog)](https://github.com/devzerops/blog/stargazers)
[![GitHub license](https://img.shields.io/github/license/devzerops/blog)](https://github.com/devzerops/blog/blob/main/LICENSE)
