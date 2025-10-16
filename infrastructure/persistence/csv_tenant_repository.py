import csv
import logging
from pathlib import Path
from domain.entities.tenant import Tenant
from domain.repositories.tenant_repository import TenantRepository


logger = logging.getLogger(__name__)


class CsvTenantRepository(TenantRepository):
    """CSV 파일 기반 테넌트 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        tenants_file: tenants.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.tenants_file = data_dir / "tenants.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.tenants_file.exists():
            with open(self.tenants_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "created_at", "is_active"])
                writer.writeheader()

    def save_tenant(self, tenant: Tenant) -> None:
        """테넌트를 CSV에 저장합니다.

        Args:
            tenant: 저장할 테넌트 엔티티
        """
        with open(self.tenants_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "created_at", "is_active"])
            writer.writerow(tenant.to_dict())
            f.flush()

    def find_tenant_by_id(self, tenant_id: str) -> Tenant | None:
        """ID로 테넌트를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            테넌트 엔티티 또는 None
        """
        tenant_id = tenant_id.strip()

        with open(self.tenants_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id == tenant_id:
                    return Tenant.from_dict(row)

        logger.warning("테넌트를 찾을 수 없습니다", extra={"tenant_id": tenant_id})
        return None

    def find_all_tenants(self) -> list[Tenant]:
        """모든 테넌트를 조회합니다.

        Returns:
            테넌트 엔티티 목록
        """
        tenants = []
        with open(self.tenants_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue
                tenants.append(Tenant.from_dict(row))
        return tenants
