"""중복 이메일 정리 스크립트

중복된 이메일을 가진 사용자 중 하나를 삭제합니다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.persistence.orm.base import create_session_factory
from infrastructure.persistence.orm.models.user import UserORM
from config import settings


def main():
    """중복 이메일을 정리합니다."""

    print("=== 중복 이메일 정리 시작 ===\n")

    # 삭제할 사용자 ID (username='admin'인 구 버전)
    user_id_to_delete = "18238881-b4c2-4d78-ae97-f397e32a0c6e"

    # 세션 팩토리 생성
    session_factory = create_session_factory(settings.database_url)

    try:
        with session_factory() as session:
            # 삭제할 사용자 조회
            user = session.query(UserORM).filter_by(id=user_id_to_delete).first()

            if not user:
                print(f"[INFO] 사용자 ID {user_id_to_delete}를 찾을 수 없습니다.")
                print("이미 정리되었거나 ID가 변경되었을 수 있습니다.")
                return

            print(f"삭제할 사용자:")
            print(f"  - User ID: {user.id}")
            print(f"  - Tenant ID: {user.tenant_id}")
            print(f"  - Username: {user.username}")
            print(f"  - Email: {user.email}\n")

            # 사용자 삭제
            session.delete(user)
            session.commit()

            print("[OK] 사용자가 삭제되었습니다.")
            print("\n이제 이메일 unique 제약조건을 안전하게 추가할 수 있습니다.")

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
