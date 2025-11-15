from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """범주 생성 요청 스키마입니다.

    Attributes:
        name: 범주 이름
        description: 범주 설명
        order: 표시 순서
    """
    name: str = Field(..., min_length=1, max_length=100, description="범주 이름")
    description: str = Field(default="", max_length=500, description="범주 설명")
    order: int = Field(default=0, ge=0, description="표시 순서")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "시설 관련",
                "description": "병원 시설에 대한 질문 그룹",
                "order": 1
            }
        }


class CategoryUpdate(BaseModel):
    """범주 수정 요청 스키마입니다.

    Attributes:
        name: 범주 이름 (선택)
        description: 범주 설명 (선택)
        order: 표시 순서 (선택)
    """
    name: str | None = Field(None, min_length=1, max_length=100, description="범주 이름")
    description: str | None = Field(None, max_length=500, description="범주 설명")
    order: int | None = Field(None, ge=0, description="표시 순서")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "수정된 범주 이름",
                "description": "수정된 범주 설명",
                "order": 2
            }
        }


class CategoryResponse(BaseModel):
    """범주 응답 스키마입니다.

    Attributes:
        id: 범주 ID
        survey_id: 설문 ID
        name: 범주 이름
        description: 범주 설명
        order: 표시 순서
    """
    id: str = Field(..., description="범주 ID")
    survey_id: str = Field(..., description="설문 ID")
    name: str = Field(..., description="범주 이름")
    description: str = Field(..., description="범주 설명")
    order: int = Field(..., description="표시 순서")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "category_123",
                "survey_id": "survey_456",
                "name": "시설 관련",
                "description": "병원 시설에 대한 질문 그룹",
                "order": 1
            }
        }


class CategoryListResponse(BaseModel):
    """범주 목록 응답 스키마입니다.

    Attributes:
        categories: 범주 목록
        total: 전체 범주 수
    """
    categories: list[CategoryResponse] = Field(default_factory=list, description="범주 목록")
    total: int = Field(..., description="전체 범주 수")

    class Config:
        json_schema_extra = {
            "example": {
                "categories": [
                    {
                        "id": "category_1",
                        "survey_id": "survey_456",
                        "name": "시설 관련",
                        "description": "병원 시설에 대한 질문",
                        "order": 1
                    },
                    {
                        "id": "category_2",
                        "survey_id": "survey_456",
                        "name": "서비스 관련",
                        "description": "직원 서비스에 대한 질문",
                        "order": 2
                    }
                ],
                "total": 2
            }
        }
