"""Tenant ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class TenantORM(Base):
    """테넌트(조직/회사) 테이블 ORM 모델

    테넌트는 시스템의 최상위 격리 단위로,
    모든 데이터는 테넌트 단위로 분리됩니다.
    """
    __tablename__ = "tenants"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[list["UserORM"]] = relationship(
        "UserORM",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    surveys: Mapped[list["SurveyORM"]] = relationship(
        "SurveyORM",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    categories: Mapped[list["CategoryORM"]] = relationship(
        "CategoryORM",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<TenantORM(id={self.id}, name={self.name})>"