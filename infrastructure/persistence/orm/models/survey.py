"""Survey 및 Question ORM 모델 정의"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.persistence.orm.base import Base


class SurveyORM(Base):
    """설문 테이블 ORM 모델

    설문은 여러 질문을 포함하며, 각 설문은 테넌트와 소유자를 가집니다.
    """
    __tablename__ = "surveys"
    __table_args__ = (
        # 테넌트별 설문 조회를 위한 인덱스
        Index("ix_surveys_tenant_id", "tenant_id"),
        # 소유자별 설문 조회를 위한 인덱스
        Index("ix_surveys_owner_id", "owner_id"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Basic Fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    tenant: Mapped["TenantORM"] = relationship(
        "TenantORM",
        back_populates="surveys",
        lazy="joined"
    )

    owner: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="owned_surveys",
        foreign_keys=[owner_id],
        lazy="joined"
    )

    questions: Mapped[list["QuestionORM"]] = relationship(
        "QuestionORM",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="QuestionORM.order",
        lazy="selectin"
    )

    survey_sessions: Mapped[list["SurveySessionORM"]] = relationship(
        "SurveySessionORM",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    responses: Mapped[list["ResponseORM"]] = relationship(
        "ResponseORM",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<SurveyORM(id={self.id}, title={self.title})>"


class QuestionORM(Base):
    """질문 테이블 ORM 모델

    각 질문은 하나의 설문에 속하며, 선택적으로 범주에 속할 수 있습니다.
    """
    __tablename__ = "questions"
    __table_args__ = (
        # 설문별 질문 조회를 위한 인덱스
        Index("ix_questions_survey_id_order", "survey_id", "order"),
        # 범주별 질문 조회를 위한 인덱스
        Index("ix_questions_category_id", "category_id"),
    )

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    survey_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False
    )

    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )

    # Basic Fields
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    options: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    survey: Mapped["SurveyORM"] = relationship(
        "SurveyORM",
        back_populates="questions",
        lazy="joined"
    )

    category: Mapped["CategoryORM | None"] = relationship(
        "CategoryORM",
        back_populates="questions",
        lazy="joined"
    )

    responses: Mapped[list["ResponseORM"]] = relationship(
        "ResponseORM",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """개발 디버깅을 위한 문자열 표현"""
        return f"<QuestionORM(id={self.id}, text={self.text[:50]}...)>"