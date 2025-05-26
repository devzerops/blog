"""
SQLite 기본 연결 테스트
"""
import sqlite3

# 메모리 데이터베이스 연결 테스트
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
except Exception as e:
    print(f"메모리 데이터베이스 오류: {e}")

# 파일 데이터베이스 연결 테스트 (현재 디렉토리)
print("\n현재 디렉토리 파일 데이터베이스 연결 테스트 중...")
try:
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)')
    cursor.execute('INSERT INTO test VALUES (1, "테스트")')
    cursor.execute('SELECT * FROM test')
    print("결과:", cursor.fetchall())
    conn.close()
    print("파일 데이터베이스 테스트 성공!")
except Exception as e:
    print(f"파일 데이터베이스 오류: {e}")

# /tmp 디렉토리 파일 데이터베이스 연결 테스트
print("\n/tmp 디렉토리 파일 데이터베이스 연결 테스트 중...")
try:
    conn = sqlite3.connect('/tmp/test.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)')
    cursor.execute('INSERT INTO test VALUES (1, "테스트")')
    cursor.execute('SELECT * FROM test')
    print("결과:", cursor.fetchall())
    conn.close()
    print("/tmp 디렉토리 파일 데이터베이스 테스트 성공!")
except Exception as e:
    print(f"/tmp 디렉토리 파일 데이터베이스 오류: {e}")
