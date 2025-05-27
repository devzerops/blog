# Python Flask Blog

모놀리틱 구조로 개발된 Flask 기반 블로그 애플리케이션입니다. JWT 토큰 기반 인증을 통해 관리자 권한을 제공합니다.

## 주요 기능

- 관리자 인증 (JWT 기반)
- 게시물 CRUD (관리자 전용)
- 카테고리 및 태그 관리
- 댓글 시스템
- 마크다운 지원 (CKEditor/TinyMCE)
- 이미지 업로드 및 최적화
- 비디오 임베딩 (URL 기반)
- 코드 블록 구문 강조 (Prism.js)
- 코드 블록 클립보드 복사
- 사이트 설정 관리
- 게시물 검색
- 게시물 상태 관리 (초안/발행)
- 페이지 뷰 추적
- 반응형 디자인

## 프로젝트 구조

```
blog/                       # 프로젝트 루트
├── app/                    # 애플리케이션 패키지
│   ├── __init__.py         # 애플리케이션 초기화 및 팩토리 함수
│   ├── database.py         # 데이터베이스 설정
│   ├── models.py           # DB 모델 (User, Post, Category, Comment, SiteSetting 등)
│   ├── routes/             # 라우트 모듈 패키지
│   │   ├── admin/          # 관리자 라우트
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── routes_admin.py     # 관리자 라우트
│   ├── routes_auth.py      # 인증 라우트
│   ├── routes_public.py    # 공개 라우트
│   ├── static/             # 정적 파일 (CSS, JS, 이미지 등)
│   │   ├── ckeditor5/
│   │   ├── css/
│   │   ├── img/
│   │   ├── js/
│   │   ├── tinymce/
│   │   ├── temp/
│   │   └── uploads/
│   └── templates/          # Jinja2 템플릿
│       ├── admin/
│       ├── components/
│       ├── macros/
│       ├── public/
│       ├── admin_base.html
│       ├── base.html
│       └── bootstrap_wtf.html
├── config.py               # 애플리케이션 설정
├── instance/               # 인스턴스별 설정 및 데이터
│   └── blog.db             # SQLite DB 파일
├── migrations/             # DB 마이그레이션
│   └── versions/
├── run.py                  # 실행 스크립트
├── requirements.txt        # 의존성 목록
└── .env                    # 환경 변수 (git 미포함)
```

## 설치 및 실행

1. **저장소 복제 또는 파일 생성**

2. **가상 환경 생성 및 활성화**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **.env 파일 작성**
   ```
   SECRET_KEY='your_very_secret_random_string_here'
   # 선택: DATABASE_URL='sqlite:///path/to/your/database.sqlite'
   ```

5. **DB 마이그레이션 및 초기화**
   ```bash
   flask db init        # 최초 1회
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **초기 데이터 생성**
   ```bash
   flask init-db
   ```

7. **애플리케이션 실행**
   ```bash
   flask run
   # 또는
   python run.py
   ```
   블로그: http://127.0.0.1:5000/

   관리자 로그인: http://127.0.0.1:5000/login

## 데이터베이스 모델

- **User**: 관리자 계정
- **Post**: 게시물 (제목, 내용, 썸네일, 상태 등)
- **Category**: 카테고리
- **Comment**: 댓글
- **SiteSetting**: 사이트 설정 (제목, 설명 등)
- **PageView**: 페이지 조회수

## 주요 기능 설명

- **관리자 대시보드**: 로그인 후 게시물, 카테고리, 댓글, 사이트 설정 관리
- **게시물 관리**: 작성, 수정, 삭제, 상태(발행/초안), 카테고리/태그 지정, 이미지/비디오 첨부
- **카테고리/태그 시스템**: 게시물 분류 및 필터링
- **댓글 시스템**: 익명 댓글, 관리자 관리
- **사이트 설정**: 제목, 설명, 파비콘, 푸터 등 설정
- **이미지 최적화**: 업로드 시 자동 최적화(크기 조정 및 압축)

## 참고

Flask 기본 구조와 확장성에 대한 설명은 [위키독스], [REAL Python], [네이버 블로그] 등에서 확인할 수 있습니다.

Flask Blueprint, 템플릿 구조, DB 마이그레이션 등은 Flask 공식 튜토리얼 및 주요 블로그 예제를 참고했습니다.


## 실행

``` 
flask db init
flask db migrate -m "Initial migration"
docker-compose exec web flask db upgrade
flask db upgrade
cd /home/server/Documents/develop/blog && export FLASK_DEBUG=1 && python -m flask run --host=0.0.0.0
 ```