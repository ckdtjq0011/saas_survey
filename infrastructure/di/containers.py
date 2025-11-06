"""Dependency Injection 컨테이너"""

from dependency_injector import containers, providers
from pathlib import Path

from infrastructure.persistence.orm.base import create_session_factory

# ORM repositories
from infrastructure.persistence.orm.repositories.tenant_repository import SqlAlchemyTenantRepository
from infrastructure.persistence.orm.repositories.user_repository import SqlAlchemyUserRepository
from infrastructure.persistence.orm.repositories.session_repository import SqlAlchemySessionRepository
from infrastructure.persistence.orm.repositories.survey_repository import SqlAlchemySurveyRepository
from infrastructure.persistence.orm.repositories.response_repository import SqlAlchemyResponseRepository
from infrastructure.persistence.orm.repositories.response_history_repository import SqlAlchemyResponseHistoryRepository
from infrastructure.persistence.orm.repositories.category_repository import SqlAlchemyCategoryRepository
from infrastructure.persistence.orm.repositories.survey_session_repository import SqlAlchemySurveySessionRepository

# CSV repositories (Backward compatibility)
from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_response_history_repository import CsvResponseHistoryRepository
from infrastructure.persistence.csv_category_repository import CsvCategoryRepository
from infrastructure.persistence.csv_survey_session_repository import CsvSurveySessionRepository

# Application services
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.survey_session_service import SurveySessionService
from application.auth_service import AuthService
from application.category_service import CategoryService

# Interface
from interface.cli.commands import Commands


class Container(containers.DeclarativeContainer):
    """DI 컨테이너 - 모든 의존성을 관리합니다."""

    # Configuration
    config = providers.Configuration()

    # Database session factory (SQLite/PostgreSQL용)
    db_session_factory = providers.Singleton(
        create_session_factory,
        database_url=config.database_url,
        echo=config.database_echo
    )

    # Data directory (CSV용)
    data_dir = providers.Factory(
        Path,
        config.data_dir
    )

    # Repositories - storage_type에 따라 선택
    tenant_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemyTenantRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvTenantRepository,
            data_dir=data_dir
        )
    )

    user_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemyUserRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvUserRepository,
            data_dir=data_dir
        )
    )

    session_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemySessionRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvSessionRepository,
            data_dir=data_dir
        )
    )

    survey_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemySurveyRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvSurveyRepository,
            data_dir=data_dir
        )
    )

    response_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemyResponseRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvResponseRepository,
            data_dir=data_dir
        )
    )

    response_history_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemyResponseHistoryRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvResponseHistoryRepository,
            data_dir=data_dir
        )
    )

    category_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemyCategoryRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvCategoryRepository,
            data_dir=data_dir
        )
    )

    survey_session_repository = providers.Selector(
        config.storage_type,
        sqlite=providers.Factory(
            SqlAlchemySurveySessionRepository,
            session_factory=db_session_factory
        ),
        csv=providers.Factory(
            CsvSurveySessionRepository,
            data_dir=data_dir
        )
    )

    # Application Services
    survey_service = providers.Factory(
        SurveyService,
        survey_repository=survey_repository
    )

    response_service = providers.Factory(
        ResponseService,
        response_repository=response_repository,
        response_history_repository=response_history_repository,
        survey_repository=survey_repository,
        category_repository=category_repository
    )

    survey_session_service = providers.Factory(
        SurveySessionService,
        survey_session_repository=survey_session_repository,
        survey_repository=survey_repository
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        session_repository=session_repository
    )

    category_service = providers.Factory(
        CategoryService,
        category_repository=category_repository
    )

    # CLI Commands
    commands = providers.Factory(
        Commands,
        survey_service=survey_service,
        response_service=response_service,
        survey_session_service=survey_session_service,
        auth_service=auth_service,
        category_service=category_service,
        tenant_repo=tenant_repository,
        user_repo=user_repository,
        debug=config.debug
    )