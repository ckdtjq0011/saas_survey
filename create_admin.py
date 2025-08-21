"""
Admin 계정 생성 스크립트
사용법: uv run python create_admin.py
"""
from app.db.base import get_db, engine, Base
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

def create_admin_user():
    """Admin 계정을 생성합니다."""
    
    # 데이터베이스 테이블 생성 (없는 경우)
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    db: Session = next(get_db())
    
    try:
        # 기존 admin 계정 확인
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("[INFO] Admin account already exists. Updating password...")
            # 자동으로 비밀번호를 admin123으로 업데이트
            existing_admin.hashed_password = get_password_hash("admin123")
            existing_admin.is_superuser = True
            existing_admin.is_active = True
            db.commit()
            print("[SUCCESS] Admin account updated!")
            print("\nAccount Information:")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Email: {existing_admin.email}")
            print(f"   Superuser: Yes")
            return
        
        # 새 admin 계정 생성
        admin_user = User(
            email="admin@hospital.com",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("[SUCCESS] Admin account created successfully!")
        print("\nAccount Information:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@hospital.com")
        print(f"   Full Name: System Administrator")
        print(f"   Superuser: Yes")
        print(f"\n[WARNING] Security Notice: Please change the password in production!")
        
    except Exception as e:
        print(f"[ERROR] Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()