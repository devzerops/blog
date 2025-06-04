#!/bin/bash
set -e

# 환경 변수 기본값 설정
POSTGRES_HOST=${POSTGRES_HOST:-db}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-blog}

echo "📦 환경 변수 설정 완료"

# PostgreSQL 연결 확인 함수
wait_for_postgres() {
    echo "⏳ PostgreSQL 연결을 기다리는 중..."
    python3 /app/wait_for_postgres.py
    if [ $? -ne 0 ]; then
        echo "❌ PostgreSQL 연결에 실패했습니다. 애플리케이션을 종료합니다."
        exit 1
    fi
}

# 메인 실행 함수
main() {
    # PostgreSQL 연결 대기
    wait_for_postgres

    # 필요한 디렉토리 생성 및 권한 설정
    echo "📂 필요한 디렉토리를 생성합니다..."
    mkdir -p /app/instance /app/app/static/uploads /app/app/static/temp
    chmod -R 777 /app/app/static

    # 마이그레이션 디렉토리 초기화 (필요한 경우)
    if [ ! -d "/app/migrations" ]; then
        echo "🔄 마이그레이션 디렉토리를 초기화합니다..."
        flask db init
    fi

    # 마이그레이션 적용
    echo "🔄 데이터베이스 마이그레이션을 적용합니다..."
    # 여러 head가 있는 경우 모든 head로 업그레이드
    flask db upgrade heads || flask db upgrade

    # 애플리케이션 실행
    echo "🚀 애플리케이션을 시작합니다..."
    exec "$@"

    # 초기 데이터베이스 생성
    echo "🔄 초기 데이터베이스를 생성합니다..."
    flask init-db
}

# 메인 함수 실행
main "$@"
