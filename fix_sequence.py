from app import create_app
from app.database import db
from sqlalchemy import text

def fix_sequence():
    app = create_app()
    with app.app_context():
        # 현재 post 테이블의 가장 큰 ID 조회
        result = db.session.execute(text('SELECT MAX(id) FROM post')).scalar()
        max_id = result if result else 0
        
        # 시퀀스를 (가장 큰 ID + 1)로 설정
        db.session.execute(text(f"SELECT setval('post_id_seq', {max_id + 1}, false)"))
        db.session.commit()
        
        print(f"시퀀스가 {max_id + 1}(으)로 재설정되었습니다.")

if __name__ == '__main__':
    fix_sequence()
