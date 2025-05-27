#!/usr/bin/env python3
import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError

def check_postgres_connection():
    """PostgreSQL 서버에 연결을 시도합니다."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'blog'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            host=os.getenv('POSTGRES_HOST', 'db'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        conn.close()
        return True
    except OperationalError:
        return False

def main():
    max_attempts = 30
    attempt = 0
    
    print("⏳ PostgreSQL 연결을 기다리는 중...")
    
    while attempt < max_attempts:
        if check_postgres_connection():
            print("✅ PostgreSQL이 정상적으로 실행 중입니다!")
            return 0
            
        attempt += 1
        print(f"⏳ PostgreSQL 연결 시도 중... ({attempt}/{max_attempts})")
        time.sleep(2)
    
    print(f"❌ {max_attempts}번의 시도 후에도 PostgreSQL에 연결할 수 없습니다.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
