"""Category ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class CategoryORM(Base):
    """범주 테이블 ORM 모델

    질문을 범주화하기 위한 계층적 구조를 지원합니다.
    parent_id를 통해 자기 참조하여 무한 계층 구조를 만들 수 있습니다.
    """
    __tablename__ = "categories"
    __table_args__ = (
        # 테넌트별 범주 조회를 위한 인덱스
        Index("ix_categories_tenant_id", "tenant_id"),
        # 계층 구조 탐색을 위한 인덱스
        Index("ix_categories_parent_id", "parent_id"),
        # 정렬된 목록 조회를 위한 인덱스
        Index("ix_categories_order", "order"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True
    )

    # Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    tenant: Mapped["TenantORM"] = relationship(
        "TenantORM",
        back_populates="categories",
        lazy="joined"
    )

    # 자기 참조 관계: 상위 범주
    parent: Mapped["CategoryORM | None"] = relationship(
        "CategoryORM",
        remote_side=[id],
        back_populates="children",
        lazy="joined"
    )

    # 자기 참조 관계: 하위 범주들
    children: Mapped[list["CategoryORM"]] = relationship(
        "CategoryORM",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    questions: Mapped[list["QuestionORM"]] = relationship(
        "QuestionORM",
        back_populates="category",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<CategoryORM(id={self.id}, name={self.name}, parent_id={self.parent_id})>"