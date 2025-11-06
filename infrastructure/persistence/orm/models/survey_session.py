"""SurveySession ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class SurveySessionORM(Base):
    """설문 응답 세션 테이블 ORM 모델

    설문 응답의 전체 과정을 추적합니다.
    응답자가 설문을 시작하고 제출하기까지의 모든 정보를 기록합니다.
    """
    __tablename__ = "survey_sessions"
    __table_args__ = (
        # 설문별 세션 조회를 위한 인덱스
        Index("ix_survey_sessions_survey_id", "survey_id"),
        # 응답자별 세션 조회를 위한 인덱스
        Index("ix_survey_sessions_respondent_id", "respondent_id"),
        # 시계열 분석을 위한 인덱스
        Index("ix_survey_sessions_started_at", "started_at"),
        Index("ix_survey_sessions_submitted_at", "submitted_at"),
        # 완료 상태별 조회를 위한 인덱스
        Index("ix_survey_sessions_completed", "completed"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    survey_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False
    )

    # Basic Fields
    respondent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    total_time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    survey: Mapped["SurveyORM"] = relationship(
        "SurveyORM",
        back_populates="survey_sessions",
        lazy="joined"
    )

    responses: Mapped[list["ResponseORM"]] = relationship(
        "ResponseORM",
        back_populates="survey_session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<SurveySessionORM(id={self.id}, survey_id={self.survey_id}, respondent_id={self.respondent_id}, completed={self.completed})>"