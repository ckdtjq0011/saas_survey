"""Response ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class ResponseORM(Base):
    """응답 테이블 ORM 모델

    각 응답은 특정 설문의 특정 질문에 대한 답변을 나타냅니다.
    응답은 세션 단위로 추적됩니다.
    """
    __tablename__ = "responses"
    __table_args__ = (
        # 세션별 응답 조회를 위한 인덱스
        Index("ix_responses_session_id", "session_id"),
        # 응답자별 응답 조회를 위한 인덱스
        Index("ix_responses_respondent_id", "respondent_id"),
        # 설문별 응답 조회를 위한 인덱스
        Index("ix_responses_survey_id", "survey_id"),
        # 질문별 응답 조회를 위한 인덱스
        Index("ix_responses_question_id", "question_id"),
        # 시계열 분석을 위한 인덱스
        Index("ix_responses_answered_at", "answered_at"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    survey_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False
    )

    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False
    )

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("survey_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Basic Fields
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    respondent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    survey: Mapped["SurveyORM"] = relationship(
        "SurveyORM",
        back_populates="responses",
        lazy="joined"
    )

    question: Mapped["QuestionORM"] = relationship(
        "QuestionORM",
        back_populates="responses",
        lazy="joined"
    )

    survey_session: Mapped["SurveySessionORM"] = relationship(
        "SurveySessionORM",
        back_populates="responses",
        lazy="joined"
    )

    histories: Mapped[list["ResponseHistoryORM"]] = relationship(
        "ResponseHistoryORM",
        back_populates="response",
        cascade="all, delete-orphan",
        order_by="ResponseHistoryORM.updated_at",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<ResponseORM(id={self.id}, respondent_id={self.respondent_id})>"