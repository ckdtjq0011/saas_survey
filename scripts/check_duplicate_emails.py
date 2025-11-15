"""중복 이메일 체크 스크립트

데이터베이스에서 중복된 이메일을 찾습니다.
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.persistence.orm.base import create_session_factory
from infrastructure.persistence.orm.models.user import UserORM
from config import settings


def main():
    """중복 이메일을 체크합니다."""

    print("=== 이메일 중복 체크 시작 ===\n")
    print(f"데이터베이스: {settings.database_url}\n")

    # 세션 팩토리 생성
    session_factory = create_session_factory(settings.database_url)

    # 모든 사용자 조회
    try:
        with session_factory() as session:
            all_users = session.query(UserORM).all()
            print(f"총 사용자 수: {len(all_users)}\n")

            if len(all_users) == 0:
                print("[INFO] 데이터베이스에 사용자가 없습니다.")
                return

            # 이메일 카운트
            email_counts = Counter(user.email for user in all_users)

            # 중복 이메일 찾기
            duplicates = {email: count for email, count in email_counts.items() if count > 1}

            if duplicates:
                print("[경고] 중복된 이메일이 발견되었습니다!\n")
                for email, count in duplicates.items():
                    print(f"  - {email}: {count}개")
                    users_with_email = [u for u in all_users if u.email == email]
                    for user in users_with_email:
                        print(f"    User ID: {user.id}, Tenant: {user.tenant_id}, Username: {user.username}")
                print(f"\n중복 이메일 개수: {len(duplicates)}")
                print("\n[액션 필요] unique 제약조건 추가 전에 중복 데이터를 정리해야 합니다.")
            else:
                print("[OK] 중복된 이메일이 없습니다.")
                print("이메일 unique 제약조건을 안전하게 추가할 수 있습니다.")

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
