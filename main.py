import json
import logging
from pathlib import Path
from interface.cli.commands import SurveyCommands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """병원 만족도 설문조사 플랫폼 MVP 데모를 실행합니다."""
    try:
        data_dir = Path("data")
        commands = SurveyCommands(data_dir)

        print("=" * 60)
        print("병원 만족도 설문조사 플랫폼 MVP 데모")
        print("=" * 60)

        print("\n1. 설문 생성")
        survey_id = commands.create_survey(
            title="2024년 병원 만족도 조사",
            description="환자분들의 병원 이용 경험을 개선하기 위한 설문입니다"
        )
        print(f"   - 설문 ID: {survey_id}")

        print("\n2. 질문 추가")
        q1_id = commands.add_question(
            survey_id=survey_id,
            text="전반적인 병원 서비스에 만족하십니까?",
            question_type="rating",
        )
        print(f"   - 평점 질문 ID: {q1_id}")

        q2_id = commands.add_question(
            survey_id=survey_id,
            text="가장 만족스러웠던 부분은 무엇입니까?",
            question_type="choice",
            options=["의료진 친절도", "대기 시간", "시설 청결도", "진료 결과"],
        )
        print(f"   - 객관식 질문 ID: {q2_id}")

        q3_id = commands.add_question(
            survey_id=survey_id,
            text="개선이 필요한 사항을 자유롭게 작성해주세요",
            question_type="text",
        )
        print(f"   - 텍스트 질문 ID: {q3_id}")

        print("\n3. 설문 조회")
        survey_data = commands.get_survey(survey_id)
        print(f"   - 제목: {survey_data['title']}")
        print(f"   - 질문 수: {len(survey_data['questions'])}")

        print("\n4. 응답 제출 (환자 3명)")
        commands.submit_response(
            survey_id=survey_id,
            respondent_id="patient_001",
            answers={
                q1_id: "5",
                q2_id: "의료진 친절도",
                q3_id: "모든 것이 만족스러웠습니다",
            }
        )
        print("   - 환자 001 응답 완료")

        commands.submit_response(
            survey_id=survey_id,
            respondent_id="patient_002",
            answers={
                q1_id: "4",
                q2_id: "시설 청결도",
                q3_id: "대기 시간이 조금 길었습니다",
            }
        )
        print("   - 환자 002 응답 완료")

        commands.submit_response(
            survey_id=survey_id,
            respondent_id="patient_003",
            answers={
                q1_id: "5",
                q2_id: "의료진 친절도",
                q3_id: "진료가 매우 만족스러웠습니다",
            }
        )
        print("   - 환자 003 응답 완료")

        print("\n5. 결과 조회")
        results = commands.get_results(survey_id)
        print(json.dumps(results, indent=2, ensure_ascii=False))

        print("\n6. 설문 목록 조회")
        surveys = commands.list_surveys()
        for survey in surveys:
            print(f"   - [{survey['id']}] {survey['title']} (질문: {survey['question_count']}개)")

        print("\n" + "=" * 60)
        print("MVP 데모 완료")
        print(f"데이터는 {data_dir.absolute()} 디렉토리에 저장되었습니다")
        print("=" * 60)

    except Exception:
        logger.exception("프로그램 실행 중 오류가 발생했습니다")
        raise


if __name__ == "__main__":
    main()
