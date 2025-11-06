"""User ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class UserORM(Base):
    """사용자 테이블 ORM 모델

    시스템 사용자를 나타내며, 각 사용자는 하나의 테넌트에 속합니다.
    역할(role)에 따라 권한이 결정됩니다.
    """
    __tablename__ = "users"
    __table_args__ = (
        # tenant_id와 username 조합이 고유해야 함
        Index("ix_users_tenant_username", "tenant_id", "username", unique=True),
        # 이메일로 조회하는 경우를 위한 인덱스
        Index("ix_users_email", "email"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic Fields
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tenant: Mapped["TenantORM"] = relationship(
        "TenantORM",
        back_populates="users",
        lazy="joined"
    )

    sessions: Mapped[list["SessionORM"]] = relationship(
        "SessionORM",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    owned_surveys: Mapped[list["SurveyORM"]] = relationship(
        "SurveyORM",
        back_populates="owner",
        foreign_keys="[SurveyORM.owner_id]",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<UserORM(id={self.id}, username={self.username}, role={self.role})>"