import csv
import logging
from pathlib import Path
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class CsvUserRepository(UserRepository):
    """CSV 파일 기반 사용자 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        users_file: users.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.users_file = data_dir / "users.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.users_file.exists():
            with open(self.users_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "tenant_id", "username", "email", "password_hash", "role", "created_at", "is_active"]
                )
                writer.writeheader()

    def save_user(self, user: User) -> None:
        """사용자를 CSV에 저장합니다.

        Args:
            user: 저장할 사용자 엔티티
        """
        with open(self.users_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "tenant_id", "username", "email", "password_hash", "role", "created_at", "is_active"]
            )
            writer.writerow(user.to_dict())
            f.flush()

    def find_user_by_id(self, user_id: str) -> User | None:
        """ID로 사용자를 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        user_id = user_id.strip()

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id == user_id:
                    return User.from_dict(row)

        logger.warning("사용자를 찾을 수 없습니다", extra={"user_id": user_id})
        return None

    def find_user_by_username(self, username: str, tenant_id: str) -> User | None:
        """사용자명으로 사용자를 조회합니다.

        Args:
            username: 사용자명
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        username = username.strip()
        tenant_id = tenant_id.strip()

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_username = row["username"].strip()
                row_tenant_id = row["tenant_id"].strip()
                if row_username == username and row_tenant_id == tenant_id:
                    return User.from_dict(row)

        return None

    def find_user_by_email(self, email: str) -> User | None:
        """이메일로 사용자를 조회합니다 (전체 테넌트 검색).

        Args:
            email: 이메일 주소

        Returns:
            사용자 엔티티 또는 None
        """
        email = email.strip()

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_email = row["email"].strip()
                if row_email == email:
                    return User.from_dict(row)

        return None

    def find_users_by_tenant(self, tenant_id: str) -> list[User]:
        """테넌트의 모든 사용자를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 목록
        """
        tenant_id = tenant_id.strip()
        users = []

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_tenant_id = row["tenant_id"].strip()
                if row_tenant_id == tenant_id:
                    users.append(User.from_dict(row))

        return users

    def update_user(self, user_id: str, **updates) -> None:
        """사용자 정보를 수정합니다.

        Args:
            user_id: 사용자 식별자
            **updates: 수정할 필드

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        user_id = user_id.strip()
        rows = []
        found = False

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == user_id:
                    found = True
                    for key, value in updates.items():
                        if key in row:
                            row[key] = str(value)
                rows.append(row)

        if not found:
            raise ValueError(f"사용자를 찾을 수 없습니다: {user_id}")

        with open(self.users_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "username", "email", "password_hash", "role", "created_at", "is_active"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("사용자 정보를 수정했습니다", extra={"user_id": user_id, "updates": updates})

    def delete_user(self, user_id: str) -> None:
        """사용자를 삭제합니다.

        Args:
            user_id: 사용자 식별자

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        user_id = user_id.strip()
        rows = []
        found = False

        with open(self.users_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == user_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"사용자를 찾을 수 없습니다: {user_id}")

        with open(self.users_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "username", "email", "password_hash", "role", "created_at", "is_active"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("사용자를 삭제했습니다", extra={"user_id": user_id})
