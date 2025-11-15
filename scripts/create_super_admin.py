"""슈퍼 관리자 생성 스크립트

시스템 테넌트와 슈퍼 관리자 계정을 생성합니다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.di.containers import Container
from infrastructure.persistence.orm.base import create_database_tables
from config import settings

# 시스템 테넌트 ID (고정값)
SYSTEM_TENANT_ID = "00000000-0000-0000-0000-000000000000"


def main():
    """시스템 테넌트 및 슈퍼 관리자를 생성합니다."""

    print("=== 슈퍼 관리자 생성 시작 ===\n")
    print(f"데이터베이스: {settings.database_url}")
    print(f"저장소 타입: {settings.storage_type}\n")

    # 데이터베이스 테이블 생성
    print("1. 데이터베이스 테이블 확인 중...")
    try:
        if settings.storage_type == "sqlite":
            create_database_tables(settings.database_url)
        print("   [OK] 테이블 확인 완료\n")
    except Exception as e:
        print(f"   [ERROR] 테이블 생성 실패: {e}\n")
        return

    # Container 설정
    container = Container()
    container.config.from_dict({
        "storage_type": settings.storage_type,
        "database_url": settings.database_url,
        "database_echo": settings.database_echo,
        "data_dir": str(settings.data_dir),
        "debug": False
    })

    # Commands 가져오기
    commands = container.commands()

    # 시스템 테넌트 생성
    print("2. 시스템 테넌트 생성 중...")
    system_tenant_name = "SYSTEM"
    try:
        # 기존 시스템 테넌트 확인
        tenant_repo = container.tenant_repository()
        existing_tenant = tenant_repo.find_tenant_by_id(SYSTEM_TENANT_ID)

        if existing_tenant:
            print(f"   [INFO] 시스템 테넌트가 이미 존재합니다: {SYSTEM_TENANT_ID}\n")
        else:
            # 수동으로 시스템 테넌트 생성 (고정 ID 사용)
            from domain.entities.tenant import Tenant
            from datetime import datetime

            system_tenant = Tenant(
                id=SYSTEM_TENANT_ID,
                name=system_tenant_name,
                created_at=datetime.now(),
                is_active=True
            )
            tenant_repo.save_tenant(system_tenant)
            print(f"   [OK] 시스템 테넌트 생성 완료: {system_tenant_name} (ID: {SYSTEM_TENANT_ID})\n")

    except Exception as e:
        print(f"   [ERROR] 시스템 테넌트 생성 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return

    # 슈퍼 관리자 계정 생성
    print("3. 슈퍼 관리자 계정 생성 중...")
    admin_email = "superadmin@system.local"
    admin_password = "SuperAdmin123!"
    admin_username = "superadmin"
    role = "super_admin"

    try:
        # 기존 계정 확인
        user_repo = container.user_repository()
        existing_user = user_repo.find_user_by_email(admin_email)

        if existing_user:
            print(f"   [INFO] 슈퍼 관리자가 이미 존재합니다: {admin_email}")
            print(f"   User ID: {existing_user.id}\n")
        else:
            success, result = commands.register_user(
                tenant_id=SYSTEM_TENANT_ID,
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role=role
            )

            if success:
                user_id = result
                print(f"   [OK] 슈퍼 관리자 계정 생성 완료 (ID: {user_id})\n")
            else:
                print(f"   [ERROR] 계정 생성 실패: {result}\n")
                return

    except Exception as e:
        print(f"   [ERROR] 계정 생성 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return

    # 로그인 테스트
    print("4. 로그인 테스트 중...")
    try:
        success, result, user = commands.login(admin_email, admin_password)

        if success:
            api_key = result
            print(f"   [OK] 로그인 성공\n")
            print("=" * 60)
            print("슈퍼 관리자 계정 정보")
            print("=" * 60)
            print(f"시스템 테넌트: {system_tenant_name}")
            print(f"시스템 테넌트 ID: {SYSTEM_TENANT_ID}")
            print(f"사용자명: {admin_username}")
            print(f"이메일: {admin_email}")
            print(f"비밀번호: {admin_password}")
            print(f"역할: {role} (전체 테넌트 접근 가능)")
            print(f"API 키: {api_key}")
            print("=" * 60)
            print("\n권한:")
            print("  - 모든 테넌트의 사용자 관리")
            print("  - 모든 테넌트의 설문 조회/관리")
            print("  - 모든 테넌트의 응답 조회")
            print("  - 크로스 테넌트 통계 추출")
            print("  - 시스템 감사 로그 조회")
            print("=" * 60)
        else:
            print(f"   [ERROR] 로그인 실패: {result}\n")
            return

    except Exception as e:
        print(f"   [ERROR] 로그인 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return

    print("\n[SUCCESS] 슈퍼 관리자 생성 완료!")


if __name__ == "__main__":
    main()
