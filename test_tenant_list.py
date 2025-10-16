"""테넌트 목록 조회 기능 테스트입니다."""

import logging
from pathlib import Path
import shutil
from interface.cli.commands import Commands


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_tenant_list() -> None:
    """테넌트 목록 조회 기능을 테스트합니다."""
    logger.info("=" * 60)
    logger.info("테넌트 목록 조회 기능 테스트")
    logger.info("=" * 60)

    # 테스트 환경 준비
    test_data_dir = Path("test_data_tenant_list")
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    test_data_dir.mkdir()

    try:
        commands = Commands(test_data_dir)

        logger.info("\n[1단계] 테넌트 3개 생성")
        tenant_ids = []
        for i in range(3):
            tenant_id = commands.register_tenant(f"병원 {chr(65+i)}")
            tenant_ids.append(tenant_id)
            logger.info(f"테넌트 {chr(65+i)} 생성: {tenant_id}")

        logger.info("\n[2단계] 테넌트 목록 조회")
        tenants = commands.list_tenants()
        logger.info(f"조회된 테넌트 수: {len(tenants)}")

        assert len(tenants) == 3, f"3개의 테넌트가 조회되어야 하지만 {len(tenants)}개 조회됨"

        logger.info("\n[3단계] 테넌트 정보 확인")
        for idx, tenant in enumerate(tenants):
            logger.info(f"\n테넌트 {idx+1}:")
            logger.info(f"  ID: {tenant['id']}")
            logger.info(f"  이름: {tenant['name']}")
            logger.info(f"  생성일: {tenant['created_at']}")
            logger.info(f"  활성화 상태: {tenant['is_active']}")

            assert tenant['id'] in tenant_ids, "조회된 테넌트 ID가 생성된 ID 목록에 없음"
            assert tenant['name'].startswith("병원"), "테넌트 이름이 예상과 다름"
            assert tenant['is_active'] == "True", "테넌트가 활성화 상태여야 함"

        logger.info("\n" + "=" * 60)
        logger.info("테스트 통과: 테넌트 목록 조회 기능 정상 작동")
        logger.info("=" * 60)

    except AssertionError as e:
        logger.error(f"\n테스트 실패: {e}")
        raise
    except Exception:
        logger.exception("\n테스트 중 오류 발생")
        raise
    finally:
        if test_data_dir.exists():
            shutil.rmtree(test_data_dir)
        logger.info(f"\n테스트 데이터 정리 완료")


if __name__ == "__main__":
    test_tenant_list()
