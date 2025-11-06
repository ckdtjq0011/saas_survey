"""ResponseHistory ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class ResponseHistoryORM(Base):
    """응답 수정 이력 테이블 ORM 모델

    응답이 수정될 때마다 수정 이력을 저장하여
    감사(Audit) 및 추적 목적으로 사용됩니다.
    """
    __tablename__ = "response_histories"
    __table_args__ = (
        # 응답별 이력 조회를 위한 인덱스
        Index("ix_response_histories_response_id", "response_id"),
        # 수정자별 이력 조회를 위한 인덱스
        Index("ix_response_histories_updated_by", "updated_by"),
        # 시계열 분석을 위한 인덱스
        Index("ix_response_histories_updated_at", "updated_at"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    response_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("responses.id", ondelete="CASCADE"),
        nullable=False
    )

    # Basic Fields
    old_answer: Mapped[str] = mapped_column(Text, nullable=False)
    new_answer: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(36), nullable=False)

    # Relationships
    response: Mapped["ResponseORM"] = relationship(
        "ResponseORM",
        back_populates="histories",
        lazy="joined"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<ResponseHistoryORM(id={self.id}, response_id={self.response_id}, updated_at={self.updated_at})>"