"""CLI 테넌트 목록 조회 데모입니다."""

import logging
from pathlib import Path
import shutil
from interface.cli.commands import Commands


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """CLI 테넌트 목록 조회 데모를 실행합니다."""
    logger.info("=" * 80)
    logger.info("CLI 테넌트 목록 조회 데모")
    logger.info("=" * 80)

    # 데모 환경 준비
    demo_data_dir = Path("demo_data_tenant")
    if demo_data_dir.exists():
        shutil.rmtree(demo_data_dir)
    demo_data_dir.mkdir()

    try:
        commands = Commands(demo_data_dir)

        logger.info("\n[시나리오] 관리자가 시스템의 모든 테넌트를 조회합니다")

        logger.info("\n[1단계] 여러 병원(테넌트) 생성")
        hospitals = [
            "서울대학교병원",
            "연세세브란스병원",
            "서울아산병원",
            "삼성서울병원",
            "가톨릭대학교 서울성모병원"
        ]

        for hospital in hospitals:
            tenant_id = commands.register_tenant(hospital)
            logger.info(f"✓ {hospital} 등록 완료 (ID: {tenant_id[:8]}...)")

        logger.info("\n[2단계] 관리자가 테넌트 목록 조회")
        tenants = commands.list_tenants()

        logger.info(f"\n{'='*80}")
        logger.info(f"{'테넌트 목록 조회 결과':^80}")
        logger.info(f"{'='*80}")
        logger.info(f"총 {len(tenants)}개의 테넌트가 등록되어 있습니다.\n")

        for idx, tenant in enumerate(tenants, 1):
            status = "✓ 활성" if tenant['is_active'] == "True" else "✗ 비활성"
            logger.info(f"[{idx}] {tenant['name']}")
            logger.info(f"    테넌트 ID: {tenant['id']}")
            logger.info(f"    생성일시: {tenant['created_at']}")
            logger.info(f"    상태: {status}")
            logger.info("")

        logger.info(f"{'='*80}")
        logger.info("\n[활용 사례]")
        logger.info("1. 사용자 등록 시 테넌트 목록을 보고 원하는 조직 선택 가능")
        logger.info("2. 시스템 관리자가 전체 테넌트 현황 파악 가능")
        logger.info("3. 로그인 전에 어떤 조직들이 시스템을 사용 중인지 확인 가능")

        logger.info("\n[데모 완료]")
        logger.info("테넌트 목록 조회 기능이 정상적으로 작동합니다!")

    finally:
        if demo_data_dir.exists():
            shutil.rmtree(demo_data_dir)
        logger.info("\n데모 데이터 정리 완료")


if __name__ == "__main__":
    main()
