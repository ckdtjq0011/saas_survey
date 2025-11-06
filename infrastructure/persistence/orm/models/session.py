"""Session ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class SessionORM(Base):
    """사용자 세션 테이블 ORM 모델

    사용자 인증 및 API 접근을 위한 세션을 관리합니다.
    각 세션은 API 키를 통해 인증되며, 만료 시간을 가집니다.
    """
    __tablename__ = "sessions"
    __table_args__ = (
        # API 키는 시스템 전체에서 고유해야 함
        Index("ix_sessions_api_key", "api_key", unique=True),
        # 사용자별 세션 조회를 위한 인덱스
        Index("ix_sessions_user_id", "user_id"),
        # 테넌트별 세션 조회를 위한 인덱스
        Index("ix_sessions_tenant_id", "tenant_id"),
        # 만료된 세션 정리를 위한 인덱스
        Index("ix_sessions_expires_at", "expires_at"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )

    # Basic Fields
    api_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    user: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="sessions",
        lazy="joined"
    )

    tenant: Mapped["TenantORM"] = relationship(
        "TenantORM",
        lazy="joined"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<SessionORM(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"