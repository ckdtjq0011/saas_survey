import csv
import logging
from pathlib import Path
from domain.entities.category import Category
from domain.repositories.category_repository import CategoryRepository


logger = logging.getLogger(__name__)


class CsvCategoryRepository(CategoryRepository):
    """CSV 파일 기반 범주 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        categories_file: categories.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.categories_file = data_dir / "categories.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.categories_file.exists():
            with open(self.categories_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "tenant_id", "name", "description", "parent_id", "order", "is_active", "created_at"]
                )
                writer.writeheader()

    def save_category(self, category: Category) -> None:
        """범주를 CSV에 저장합니다.

        Args:
            category: 저장할 범주 엔티티
        """
        with open(self.categories_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "tenant_id", "name", "description", "parent_id", "order", "is_active", "created_at"]
            )
            writer.writerow(category.to_dict())
            f.flush()

    def find_category_by_id(self, category_id: str) -> Category | None:
        """ID로 범주를 조회합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            범주 엔티티 또는 None
        """
        category_id = category_id.strip()

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id == category_id:
                    return Category.from_dict(row)

        logger.warning("범주를 찾을 수 없습니다", extra={"category_id": category_id})
        return None

    def find_all_categories(self) -> list[Category]:
        """모든 범주를 조회합니다.

        Returns:
            범주 엔티티 목록
        """
        categories = []
        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue
                categories.append(Category.from_dict(row))
        return categories

    def find_by_tenant_id(self, tenant_id: str) -> list[Category]:
        """테넌트 ID로 범주 목록을 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록
        """
        tenant_id = tenant_id.strip()
        categories = []

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row.get("tenant_id", "").strip() == tenant_id:
                    categories.append(Category.from_dict(row))

        return categories

    def find_by_parent_id(self, parent_id: str | None, tenant_id: str) -> list[Category]:
        """상위 범주 ID로 하위 범주 목록을 조회합니다.

        Args:
            parent_id: 상위 범주 식별자 (None이면 최상위 범주)
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록 (order 순으로 정렬)
        """
        tenant_id = tenant_id.strip()
        categories = []

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row.get("tenant_id", "").strip() != tenant_id:
                    continue

                row_parent_id = row.get("parent_id", "").strip()

                if parent_id is None:
                    if not row_parent_id:
                        categories.append(Category.from_dict(row))
                else:
                    if row_parent_id == parent_id.strip():
                        categories.append(Category.from_dict(row))

        categories.sort(key=lambda c: c.order)
        return categories

    def update_category(self, category_id: str, **updates) -> None:
        """범주 정보를 수정합니다.

        Args:
            category_id: 범주 식별자
            **updates: 수정할 필드

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        category_id = category_id.strip()
        rows = []
        found = False

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == category_id:
                    found = True
                    for key, value in updates.items():
                        if key in row:
                            row[key] = str(value)
                rows.append(row)

        if not found:
            raise ValueError(f"범주를 찾을 수 없습니다: {category_id}")

        with open(self.categories_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "name", "description", "parent_id", "order", "is_active", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("범주 정보를 수정했습니다", extra={"category_id": category_id, "updates": updates})

    def delete_category(self, category_id: str) -> None:
        """범주를 삭제합니다.

        Args:
            category_id: 범주 식별자

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        category_id = category_id.strip()
        rows = []
        found = False

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == category_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"범주를 찾을 수 없습니다: {category_id}")

        with open(self.categories_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "name", "description", "parent_id", "order", "is_active", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("범주를 삭제했습니다", extra={"category_id": category_id})

    def has_subcategories(self, category_id: str) -> bool:
        """범주에 하위 범주가 있는지 확인합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            하위 범주가 있으면 True, 없으면 False
        """
        category_id = category_id.strip()

        with open(self.categories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_parent_id = row.get("parent_id", "").strip()
                if row_parent_id == category_id:
                    return True

        return False
