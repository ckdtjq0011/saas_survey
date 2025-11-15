"""테스트 계정 생성 스크립트

기존 CLI Commands를 사용하여 테스트 테넌트와 관리자 계정을 생성합니다.

Usage:
    python scripts/add_test_account.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.di.containers import Container
from infrastructure.persistence.orm.base import create_database_tables
from config import settings


def main():
    """테스트 계정을 생성합니다."""

    print("=== 테스트 계정 생성 시작 ===\n")
    print(f"데이터베이스: {settings.database_url}")
    print(f"저장소 타입: {settings.storage_type}\n")

    # 데이터베이스 테이블 생성
    print("1. 데이터베이스 테이블 생성 중...")
    try:
        if settings.storage_type == "sqlite":
            create_database_tables(settings.database_url)
        print("   [OK] 테이블 생성 완료\n")
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

    # Commands 가져오기 (기존 CLI 인프라 사용)
    commands = container.commands()

    # 테넌트 생성
    print("2. 테넌트 생성 중...")
    tenant_name = "Hospital"
    try:
        tenant_id = commands.register_tenant(tenant_name)
        print(f"   [OK] 테넌트 생성 완료: {tenant_name} (ID: {tenant_id})\n")
    except Exception as e:
        print(f"   [ERROR] 테넌트 생성 실패: {e}\n")
        return

    # 관리자 계정 생성
    print("3. 관리자 계정 생성 중...")
    username = "admin@hospital.com"
    email = "admin@hospital.com"
    password = "password123"
    role = "tenant_admin"

    try:
        success, result = commands.register_user(
            tenant_id=tenant_id,
            username=username,
            email=email,
            password=password,
            role=role
        )

        if success:
            user_id = result
            print(f"   [OK] 관리자 계정 생성 완료 (ID: {user_id})\n")
        else:
            print(f"   [ERROR] 계정 생성 실패: {result}\n")
            return
    except Exception as e:
        print(f"   [ERROR] 계정 생성 실패: {e}\n")
        return

    # 로그인 테스트
    print("4. 로그인 테스트 중...")
    try:
        success, result, user = commands.login(
            username=username,
            password=password,
            tenant_id=tenant_id
        )

        if success:
            api_key = result
            print(f"   [OK] 로그인 성공\n")
            print("=" * 50)
            print("테스트 계정 정보")
            print("=" * 50)
            print(f"테넌트: {tenant_name}")
            print(f"테넌트 ID: {tenant_id}")
            print(f"사용자명: {username}")
            print(f"이메일: {email}")
            print(f"비밀번호: {password}")
            print(f"역할: {role}")
            print(f"API 키: {api_key}")
            print("=" * 50)
        else:
            print(f"   [ERROR] 로그인 실패: {result}\n")
            return
    except Exception as e:
        print(f"   [ERROR] 로그인 실패: {e}\n")
        return

    print("\n[SUCCESS] 테스트 계정 생성 완료!")


if __name__ == "__main__":
    main()
