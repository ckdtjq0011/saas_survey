from dataclasses import dataclass
from domain.value_objects.types import QuestionType


@dataclass(frozen=True, slots=True)
class Question:
    """설문의 질문을 나타내는 엔티티입니다.

    Attributes:
        id: 질문 고유 식별자
        survey_id: 소속된 설문 식별자
        text: 질문 내용
        question_type: 질문 유형
        options: 객관식 선택지 (객관식인 경우)
        category_id: 소속 범주 식별자 (선택 사항)
    """
    id: str
    survey_id: str
    text: str
    question_type: QuestionType
    options: tuple[str, ...] | None = None
    category_id: str | None = None

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("질문 ID는 필수입니다")
        if not self.survey_id:
            raise ValueError("설문 ID는 필수입니다")
        if not self.text or not self.text.strip():
            raise ValueError("질문 내용은 필수입니다")
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if not self.options or len(self.options) < 2:
                raise ValueError("객관식 질문은 최소 2개 이상의 선택지가 필요합니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        # 파이프 문자를 옵션에 사용할 수 있도록 Unit Separator(ASCII 31)로 구분
        OPTIONS_DELIMITER = "\x1f"
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "text": self.text,
            "question_type": self.question_type.value,
            "options": OPTIONS_DELIMITER.join(self.options) if self.options else "",
            "category_id": self.category_id if self.category_id else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Question":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Question 엔티티 인스턴스
        """
        OPTIONS_DELIMITER = "\x1f"
        options_str = data.get("options", "")

        # Backward compatibility: 기존 파이프 구분자도 지원
        if options_str:
            if OPTIONS_DELIMITER in options_str:
                options = tuple(options_str.split(OPTIONS_DELIMITER))
            elif "|" in options_str:
                # 기존 데이터 호환성
                options = tuple(options_str.split("|"))
            else:
                options = (options_str,) if options_str else None
        else:
            options = None

        # Backward compatibility: category_id가 없는 기존 데이터 지원
        category_id = data.get("category_id", "")

        return cls(
            id=data["id"],
            survey_id=data["survey_id"],
            text=data["text"],
            question_type=QuestionType(data["question_type"]),
            options=options,
            category_id=category_id if category_id else None,
        )
