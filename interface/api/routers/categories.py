from fastapi import APIRouter, Depends, status
from loguru import logger

from interface.api.dependencies import get_category_service, require_manager, get_current_user
from interface.api.exceptions import handle_result
from interface.api.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse
)
from interface.api.schemas.common import MessageResponse
from application.category_service import CategoryService
from domain.entities.user import User


router = APIRouter(prefix="/categories", tags=["범주 관리"])


@router.post(
    "/surveys/{survey_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="범주 생성"
)
async def create_category(
    survey_id: str,
    request: CategoryCreate,
    current_user: User = Depends(require_manager()),
    service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    """범주를 생성합니다."""
    logger.info(f"범주 생성 요청: survey_id={survey_id}")

    result = service.create_category(
        survey_id=survey_id,
        name=request.name,
        description=request.description,
        order=request.order
    )
    category = handle_result(result)

    logger.info(f"범주 생성 성공: category_id={category.id}")
    return CategoryResponse(
        id=category.id,
        survey_id=category.survey_id,
        name=category.name,
        description=category.description,
        order=category.order
    )


@router.get(
    "/surveys/{survey_id}/categories",
    response_model=CategoryListResponse,
    summary="범주 목록 조회"
)
async def list_categories(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service)
) -> CategoryListResponse:
    """범주 목록을 조회합니다."""
    result = service.get_categories_by_survey(survey_id)
    categories = handle_result(result)

    return CategoryListResponse(
        categories=[
            CategoryResponse(
                id=c.id,
                survey_id=c.survey_id,
                name=c.name,
                description=c.description,
                order=c.order
            )
            for c in categories
        ],
        total=len(categories)
    )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="범주 수정"
)
async def update_category(
    category_id: str,
    request: CategoryUpdate,
    current_user: User = Depends(require_manager()),
    service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    """범주를 수정합니다."""
    result = service.update_category(
        category_id=category_id,
        name=request.name,
        description=request.description,
        order=request.order
    )
    category = handle_result(result)

    return CategoryResponse(
        id=category.id,
        survey_id=category.survey_id,
        name=category.name,
        description=category.description,
        order=category.order
    )


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="범주 삭제"
)
async def delete_category(
    category_id: str,
    current_user: User = Depends(require_manager()),
    service: CategoryService = Depends(get_category_service)
) -> MessageResponse:
    """범주를 삭제합니다."""
    result = service.delete_category(category_id)
    handle_result(result)
    return MessageResponse(message="범주가 삭제되었습니다")
