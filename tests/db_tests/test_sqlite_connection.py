"""
SQLite 기본 연결 테스트
다양한 SQLite 연결 방식을 테스트하여 데이터베이스 연결 문제를 진단합니다.
"""
import sqlite3
import os
import sys

def test_memory_db():
    """메모리 데이터베이스 연결 테스트"""
    print("메모리 데이터베이스 연결 테스트 중...")
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('INSERT INTO test VALUES (1, "테스트")')
        cursor.execute('SELECT * FROM test')
        print("결과:", cursor.fetchall())
        conn.close()
        print("메모리 데이터베이스 테스트 성공!")
        return True
    except Exception as e:
        print(f"메모리 데이터베이스 오류: {e}")
        return False

def test_file_db(db_path='test.db'):
    """파일 데이터베이스 연결 테스트"""
    print(f"\n파일 데이터베이스 연결 테스트 중... (경로: {db_path})")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('INSERT INTO test VALUES (1, "테스트")')
        cursor.execute('SELECT * FROM test')
        print("결과:", cursor.fetchall())
        conn.close()
        print(f"파일 데이터베이스 테스트 성공! (경로: {db_path})")
        return True
    except Exception as e:
        print(f"파일 데이터베이스 오류: {e}")
        return False

def run_all_tests():
    """모든 데이터베이스 연결 테스트 실행"""
    test_memory_db()
    test_file_db()
    test_file_db('/tmp/test.db')
    
    # 프로젝트 실제 데이터베이스 테스트
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    test_file_db(os.path.join(project_root, 'blog.db'))

if __name__ == "__main__":
    run_all_tests()
