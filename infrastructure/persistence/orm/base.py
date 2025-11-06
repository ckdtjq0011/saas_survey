"""SQLAlchemy Base 클래스 및 세션 팩토리 설정"""

from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import NullPool, StaticPool


class Base(DeclarativeBase):
    """모든 ORM 모델의 기본 클래스"""
    pass


def create_session_factory(
    database_url: str,
    echo: bool = False,
    **engine_kwargs: Any
) -> sessionmaker[Session]:
    """
    데이터베이스 세션 팩토리를 생성합니다.

    Args:
        database_url: 데이터베이스 연결 URL
        echo: SQL 쿼리 로깅 여부
        **engine_kwargs: 추가 엔진 설정

    Returns:
        sessionmaker 인스턴스
    """
    # SQLite in-memory 데이터베이스를 위한 특별 처리
    if database_url == "sqlite:///:memory:":
        engine = create_engine(
            database_url,
            echo=echo,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            **engine_kwargs
        )
    # 일반 SQLite 파일 데이터베이스
    elif database_url.startswith("sqlite:///"):
        engine = create_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
            **engine_kwargs
        )
    # PostgreSQL 등 다른 데이터베이스
    else:
        engine = create_engine(
            database_url,
            echo=echo,
            **engine_kwargs
        )

    return sessionmaker(bind=engine, expire_on_commit=False)


def create_database_tables(database_url: str) -> None:
    """
    데이터베이스 테이블을 생성합니다.

    Args:
        database_url: 데이터베이스 연결 URL
    """
    from infrastructure.persistence.orm.models import (
        TenantORM, UserORM, SessionORM,
        SurveyORM, QuestionORM,
        ResponseORM, ResponseHistoryORM,
        CategoryORM, SurveySessionORM
    )

    if database_url == "sqlite:///:memory:":
        engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
    elif database_url.startswith("sqlite:///"):
        engine = create_engine(
            database_url,
            poolclass=NullPool,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(database_url)

    Base.metadata.create_all(bind=engine)