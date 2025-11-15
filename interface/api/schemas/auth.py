from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator
from domain.value_objects.role import Role


class TenantCreate(BaseModel):
    """테넌트 생성 요청 스키마입니다.

    Attributes:
        name: 테넌트 이름
    """
    name: str = Field(..., min_length=2, max_length=100, description="테넌트 이름")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "우리병원"
            }
        }


class TenantResponse(BaseModel):
    """테넌트 응답 스키마입니다.

    Attributes:
        id: 테넌트 ID
        name: 테넌트 이름
        created_at: 생성 일시
        is_active: 활성화 여부
    """
    id: str = Field(..., description="테넌트 ID")
    name: str = Field(..., description="테넌트 이름")
    created_at: datetime = Field(..., description="생성 일시")
    is_active: bool = Field(..., description="활성화 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tenant_123",
                "name": "우리병원",
                "created_at": "2025-11-11T10:00:00",
                "is_active": True
            }
        }


class UserRegister(BaseModel):
    """사용자 등록 요청 스키마입니다.

    Attributes:
        tenant_id: 테넌트 ID
        username: 사용자 이름
        email: 이메일
        password: 비밀번호
        role: 역할
    """
    tenant_id: str = Field(..., min_length=1, description="테넌트 ID")
    username: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    role: str = Field(default="RESPONDENT", description="역할 (TENANT_ADMIN, SURVEY_MANAGER, RESPONDENT)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """역할 유효성 검사입니다.

        Args:
            v: 역할 문자열

        Returns:
            검증된 역할 문자열

        Raises:
            ValueError: 유효하지 않은 역할
        """
        try:
            Role[v]
        except KeyError:
            raise ValueError(f"유효하지 않은 역할입니다: {v}. 가능한 값: TENANT_ADMIN, SURVEY_MANAGER, RESPONDENT")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_123",
                "username": "홍길동",
                "email": "hong@example.com",
                "password": "SecurePass123!",
                "role": "SURVEY_MANAGER"
            }
        }


class UserLogin(BaseModel):
    """사용자 로그인 요청 스키마입니다.

    Attributes:
        email: 이메일 주소
        password: 비밀번호
    """
    email: str = Field(..., min_length=1, description="이메일 주소")
    password: str = Field(..., min_length=1, description="비밀번호")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@hospital.com",
                "password": "password123"
            }
        }


class LoginResponse(BaseModel):
    """로그인 응답 스키마입니다.

    Attributes:
        api_key: API 키
        user_id: 사용자 ID
        username: 사용자 이름
        role: 역할
        expires_at: 세션 만료 일시
        message: 메시지
    """
    api_key: str = Field(..., description="API 키 (X-API-Key 헤더에 사용)")
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자 이름")
    role: str = Field(..., description="역할")
    expires_at: datetime = Field(..., description="세션 만료 일시")
    message: str = Field(default="로그인 성공", description="메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "session_abc123xyz",
                "user_id": "user_456",
                "username": "홍길동",
                "role": "SURVEY_MANAGER",
                "expires_at": "2025-12-11T10:00:00",
                "message": "로그인 성공"
            }
        }


class UserResponse(BaseModel):
    """사용자 응답 스키마입니다.

    Attributes:
        id: 사용자 ID
        tenant_id: 테넌트 ID
        username: 사용자 이름
        email: 이메일
        role: 역할
        created_at: 생성 일시
        is_active: 활성화 여부
    """
    id: str = Field(..., description="사용자 ID")
    tenant_id: str = Field(..., description="테넌트 ID")
    username: str = Field(..., description="사용자 이름")
    email: str = Field(..., description="이메일")
    role: str = Field(..., description="역할")
    created_at: datetime = Field(..., description="생성 일시")
    is_active: bool = Field(..., description="활성화 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user_456",
                "tenant_id": "tenant_123",
                "username": "홍길동",
                "email": "hong@example.com",
                "role": "SURVEY_MANAGER",
                "created_at": "2025-11-11T10:00:00",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """사용자 수정 요청 스키마입니다.

    Attributes:
        username: 사용자 이름 (선택)
        email: 이메일 (선택)
        role: 역할 (선택)
        is_active: 활성화 여부 (선택)
    """
    username: str | None = Field(None, min_length=2, max_length=50, description="사용자 이름")
    email: EmailStr | None = Field(None, description="이메일")
    role: str | None = Field(None, description="역할")
    is_active: bool | None = Field(None, description="활성화 여부")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """역할 유효성 검사입니다.

        Args:
            v: 역할 문자열

        Returns:
            검증된 역할 문자열

        Raises:
            ValueError: 유효하지 않은 역할
        """
        if v is None:
            return v

        try:
            Role[v]
        except KeyError:
            raise ValueError(f"유효하지 않은 역할입니다: {v}. 가능한 값: TENANT_ADMIN, SURVEY_MANAGER, RESPONDENT")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "홍길동_수정",
                "email": "hong_new@example.com",
                "role": "TENANT_ADMIN",
                "is_active": False
            }
        }
