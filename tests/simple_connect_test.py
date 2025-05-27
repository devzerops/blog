import sys
import os
import psycopg2

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TestConfig

def test_postgres_connection():
    """PostgreSQL 데이터베이스에 간단하게 연결 테스트"""
    try:
        # PostgreSQL에 연결
        conn = psycopg2.connect(
            dbname=TestConfig.POSTGRES_TEST_DB,
            user=TestConfig.POSTGRES_TEST_USER,
            password=TestConfig.POSTGRES_TEST_PASSWORD,
            host=TestConfig.POSTGRES_TEST_HOST,
            port=TestConfig.POSTGRES_TEST_PORT
        )
        
        # 커서 생성
        cur = conn.cursor()
        
        # 간단한 쿼리 실행
        cur.execute('SELECT version()')
        version = cur.fetchone()
        print(f"✅ PostgreSQL 연결 성공!")
        print(f"📊 PostgreSQL 버전: {version[0]}")
        
        # 현재 데이터베이스 이름 확인
        cur.execute('SELECT current_database()')
        db_name = cur.fetchone()[0]
        print(f"💾 현재 데이터베이스: {db_name}")
        
        # 테이블 목록 조회
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [table[0] for table in cur.fetchall()]
        print(f"📋 테이블 목록: {tables}")
        
        # 연결 종료
        cur.close()
        conn.close()
        print("✅ 연결이 안전하게 종료되었습니다.")
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        raise

if __name__ == "__main__":
    test_postgres_connection()
