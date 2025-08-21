"""
Export API endpoints v1.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_export_service, get_current_user
from app.services import ExportService
from app.models.user import User

router = APIRouter()


@router.get("/{survey_id}/csv")
async def export_csv(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
) -> StreamingResponse:
    """Export survey responses as CSV."""
    return export_service.export_responses_csv(survey_id, current_user.id)


@router.get("/{survey_id}/json")
async def export_json(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
) -> StreamingResponse:
    """Export survey responses as JSON."""
    return export_service.export_responses_json(survey_id, current_user.id)


@router.get("/{survey_id}/statistics")
async def export_statistics(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """Get survey statistics."""
    return export_service.export_statistics(survey_id, current_user.id)