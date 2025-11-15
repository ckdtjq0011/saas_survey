import csv
import logging
from datetime import datetime
from pathlib import Path

from domain.entities.audit_log import AuditLog
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.value_objects.audit_action import AuditAction


logger = logging.getLogger(__name__)


class CsvAuditLogRepository(AuditLogRepository):
    """CSV 파일 기반 감사 로그 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        audit_logs_file: audit_logs.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.audit_logs_file = data_dir / "audit_logs.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.audit_logs_file.exists():
            with open(self.audit_logs_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id", "timestamp", "tenant_id", "user_id", "action",
                        "resource_type", "resource_id", "result", "ip_address", "details"
                    ]
                )
                writer.writeheader()

    def save(self, audit_log: AuditLog) -> None:
        """감사 로그를 CSV에 저장합니다.

        Args:
            audit_log: 저장할 감사 로그 엔티티
        """
        with open(self.audit_logs_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id", "timestamp", "tenant_id", "user_id", "action",
                    "resource_type", "resource_id", "result", "ip_address", "details"
                ]
            )
            writer.writerow({
                "id": audit_log.id,
                "timestamp": audit_log.timestamp.isoformat(),
                "tenant_id": audit_log.tenant_id,
                "user_id": audit_log.user_id or "",
                "action": audit_log.action.value,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id or "",
                "result": audit_log.result,
                "ip_address": audit_log.ip_address or "",
                "details": audit_log.details or ""
            })
            f.flush()

    def find_by_tenant(
        self,
        tenant_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """테넌트별 감사 로그를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        tenant_id = tenant_id.strip()
        logs = []

        with open(self.audit_logs_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["tenant_id"].strip() != tenant_id:
                    continue

                log = self._row_to_audit_log(row)
                if self._is_in_date_range(log.timestamp, start_date, end_date):
                    logs.append(log)

                if len(logs) >= limit:
                    break

        return logs

    def find_by_user(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """사용자별 감사 로그를 조회합니다.

        Args:
            user_id: 사용자 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        user_id = user_id.strip()
        logs = []

        with open(self.audit_logs_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_user_id = row["user_id"].strip()
                if row_user_id and row_user_id == user_id:
                    log = self._row_to_audit_log(row)
                    if self._is_in_date_range(log.timestamp, start_date, end_date):
                        logs.append(log)

                    if len(logs) >= limit:
                        break

        return logs

    def find_by_action(
        self,
        action: AuditAction,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """액션별 감사 로그를 조회합니다.

        Args:
            action: 액션 타입
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        logs = []

        with open(self.audit_logs_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["action"].strip() == action.value:
                    log = self._row_to_audit_log(row)
                    if self._is_in_date_range(log.timestamp, start_date, end_date):
                        logs.append(log)

                    if len(logs) >= limit:
                        break

        return logs

    def count(self) -> int:
        """전체 감사 로그 개수를 반환합니다.

        Returns:
            감사 로그 개수
        """
        count = 0

        with open(self.audit_logs_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get("id"):
                    count += 1

        return count

    def _row_to_audit_log(self, row: dict) -> AuditLog:
        """CSV 행을 AuditLog 엔티티로 변환합니다.

        Args:
            row: CSV 행 데이터

        Returns:
            AuditLog 엔티티
        """
        return AuditLog(
            id=row["id"].strip(),
            timestamp=datetime.fromisoformat(row["timestamp"].strip()),
            tenant_id=row["tenant_id"].strip(),
            user_id=row["user_id"].strip() if row["user_id"].strip() else None,
            action=AuditAction(row["action"].strip()),
            resource_type=row["resource_type"].strip(),
            resource_id=row["resource_id"].strip() if row["resource_id"].strip() else None,
            result=row["result"].strip(),
            ip_address=row["ip_address"].strip() if row["ip_address"].strip() else None,
            details=row["details"].strip() if row["details"].strip() else None
        )

    def _is_in_date_range(
        self,
        timestamp: datetime,
        start_date: datetime | None,
        end_date: datetime | None
    ) -> bool:
        """타임스탬프가 날짜 범위 내에 있는지 확인합니다.

        Args:
            timestamp: 확인할 타임스탬프
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            날짜 범위 내에 있으면 True
        """
        if start_date and timestamp < start_date:
            return False
        if end_date and timestamp > end_date:
            return False
        return True
