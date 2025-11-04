from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SurveySession:
    """설문 응답 세션을 나타내는 엔티티입니다.

    설문 시작부터 제출까지의 전체 과정을 추적합니다.

    Attributes:
        id: 세션 고유 식별자
        survey_id: 설문 식별자
        respondent_id: 응답자 식별자
        started_at: 설문 시작 시점
        submitted_at: 설문 제출 시점 (미제출 시 None)
        completed: 완료 여부
        completion_percentage: 진행률 (0-100)
        user_agent: 브라우저/디바이스 정보
        total_time_spent_seconds: 총 소요 시간 (초)
    """
    id: str
    survey_id: str
    respondent_id: str
    started_at: datetime
    submitted_at: datetime | None
    completed: bool
    completion_percentage: int
    user_agent: str
    total_time_spent_seconds: int

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("세션 ID는 필수입니다")
        if not self.survey_id:
            raise ValueError("설문 ID는 필수입니다")
        if not self.respondent_id:
            raise ValueError("응답자 ID는 필수입니다")
        if not self.user_agent:
            raise ValueError("user_agent는 필수입니다")
        if self.completion_percentage < 0 or self.completion_percentage > 100:
            raise ValueError("진행률은 0-100 사이여야 합니다")
        if self.total_time_spent_seconds < 0:
            raise ValueError("소요 시간은 음수가 될 수 없습니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "respondent_id": self.respondent_id,
            "started_at": self.started_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else "",
            "completed": str(self.completed),
            "completion_percentage": str(self.completion_percentage),
            "user_agent": self.user_agent,
            "total_time_spent_seconds": str(self.total_time_spent_seconds),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "SurveySession":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            SurveySession 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            survey_id=data["survey_id"],
            respondent_id=data["respondent_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            submitted_at=datetime.fromisoformat(data["submitted_at"]) if data["submitted_at"] else None,
            completed=data["completed"].lower() == "true",
            completion_percentage=int(data["completion_percentage"]),
            user_agent=data["user_agent"],
            total_time_spent_seconds=int(data["total_time_spent_seconds"]),
        )
