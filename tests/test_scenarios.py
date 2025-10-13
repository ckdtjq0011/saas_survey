import pytest
import csv
from pathlib import Path


class TestScenario01:
    """시나리오 1: 병원 설문 생성부터 결과 조회까지 전체 흐름 테스트"""

    def test_complete_survey_workflow(self, survey_commands, temp_data_dir):
        """병원 관리자가 설문을 생성하고 환자가 응답하는 전체 시나리오를 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처
            temp_data_dir: 임시 데이터 디렉토리 픽스처

        시나리오:
            1. 병원 관리자가 만족도 설문 생성
            2. 질문 3개 추가 (평점형, 객관식, 텍스트형)
            3. 환자 1명이 응답 제출
            4. 설문 조회 및 검증
            5. 결과 조회 및 검증
        """
        survey_id = survey_commands.create_survey(
            title="2024년 병원 만족도 조사",
            description="환자 경험 개선을 위한 설문입니다"
        )
        assert survey_id is not None
        assert len(survey_id) > 0

        q1_id = survey_commands.add_question(
            survey_id=survey_id,
            text="전반적인 병원 서비스에 만족하십니까?",
            question_type="rating"
        )
        assert q1_id is not None

        q2_id = survey_commands.add_question(
            survey_id=survey_id,
            text="가장 만족스러웠던 부분은?",
            question_type="choice",
            options=["의료진", "시설", "대기시간", "진료"]
        )
        assert q2_id is not None

        q3_id = survey_commands.add_question(
            survey_id=survey_id,
            text="개선 사항을 작성해주세요",
            question_type="text"
        )
        assert q3_id is not None

        survey_data = survey_commands.get_survey(survey_id)
        assert survey_data["id"] == survey_id
        assert survey_data["title"] == "2024년 병원 만족도 조사"
        assert len(survey_data["questions"]) == 3

        survey_commands.submit_response(
            survey_id=survey_id,
            respondent_id="patient_001",
            answers={
                q1_id: "5",
                q2_id: "의료진",
                q3_id: "매우 만족합니다"
            }
        )

        results = survey_commands.get_results(survey_id)
        assert q1_id in results
        assert results[q1_id]["count"] == 1
        assert results[q1_id]["average"] == 5.0
        assert results[q2_id]["distribution"]["의료진"] == 1
        assert "매우 만족합니다" in results[q3_id]["answers"]


class TestScenario02:
    """시나리오 2: 다양한 질문 유형 테스트"""

    def test_all_question_types(self, survey_commands):
        """모든 질문 유형이 올바르게 작동하는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 설문 생성
            2. 각 질문 유형 추가 (TEXT, RATING, MULTIPLE_CHOICE)
            3. 각 유형별로 응답 제출
            4. 각 유형별 결과 검증
        """
        survey_id = survey_commands.create_survey(
            title="질문 유형 테스트",
            description="모든 질문 유형을 테스트합니다"
        )

        text_q = survey_commands.add_question(
            survey_id=survey_id,
            text="자유 의견을 작성해주세요",
            question_type="text"
        )

        rating_q = survey_commands.add_question(
            survey_id=survey_id,
            text="평점을 매겨주세요",
            question_type="rating"
        )

        choice_q = survey_commands.add_question(
            survey_id=survey_id,
            text="선택해주세요",
            question_type="choice",
            options=["옵션1", "옵션2", "옵션3"]
        )

        survey_commands.submit_response(
            survey_id=survey_id,
            respondent_id="test_user",
            answers={
                text_q: "이것은 텍스트 응답입니다",
                rating_q: "4",
                choice_q: "옵션2"
            }
        )

        results = survey_commands.get_results(survey_id)

        assert results[text_q]["type"] == "text"
        assert results[text_q]["answers"][0] == "이것은 텍스트 응답입니다"

        assert results[rating_q]["type"] == "rating"
        assert results[rating_q]["average"] == 4.0

        assert results[choice_q]["type"] == "choice"
        assert results[choice_q]["distribution"]["옵션2"] == 1


class TestScenario03:
    """시나리오 3: 여러 응답자의 응답 처리"""

    def test_multiple_respondents(self, survey_commands):
        """여러 응답자의 응답이 올바르게 집계되는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 설문 생성 및 질문 추가
            2. 10명의 응답자가 응답 제출
            3. 통계 결과 검증 (평균, 분포 등)
        """
        survey_id = survey_commands.create_survey(
            title="다중 응답자 테스트",
            description="통계 집계 테스트"
        )

        rating_q = survey_commands.add_question(
            survey_id=survey_id,
            text="만족도를 평가해주세요",
            question_type="rating"
        )

        choice_q = survey_commands.add_question(
            survey_id=survey_id,
            text="선호하는 진료 시간대는?",
            question_type="choice",
            options=["오전", "오후", "저녁"]
        )

        responses_data = [
            ("patient_001", "5", "오전"),
            ("patient_002", "4", "오전"),
            ("patient_003", "5", "오후"),
            ("patient_004", "3", "오전"),
            ("patient_005", "4", "저녁"),
            ("patient_006", "5", "오후"),
            ("patient_007", "4", "오전"),
            ("patient_008", "5", "저녁"),
            ("patient_009", "3", "오후"),
            ("patient_010", "4", "오전"),
        ]

        for respondent_id, rating, choice in responses_data:
            survey_commands.submit_response(
                survey_id=survey_id,
                respondent_id=respondent_id,
                answers={
                    rating_q: rating,
                    choice_q: choice
                }
            )

        results = survey_commands.get_results(survey_id)

        assert results[rating_q]["count"] == 10
        expected_avg = (5 + 4 + 5 + 3 + 4 + 5 + 4 + 5 + 3 + 4) / 10
        assert results[rating_q]["average"] == expected_avg

        assert results[choice_q]["count"] == 10
        assert results[choice_q]["distribution"]["오전"] == 5
        assert results[choice_q]["distribution"]["오후"] == 3
        assert results[choice_q]["distribution"]["저녁"] == 2


class TestScenario04:
    """시나리오 4: 에러 케이스 테스트"""

    def test_invalid_survey_id(self, survey_commands):
        """존재하지 않는 설문 ID로 조회 시 에러가 발생하는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 존재하지 않는 설문 ID로 조회 시도
            2. ValueError 발생 확인
        """
        with pytest.raises(ValueError, match="설문을 찾을 수 없습니다"):
            survey_commands.get_survey("invalid_survey_id")

    def test_add_question_to_nonexistent_survey(self, survey_commands):
        """존재하지 않는 설문에 질문 추가 시 에러가 발생하는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 존재하지 않는 설문 ID에 질문 추가 시도
            2. ValueError 발생 확인
        """
        with pytest.raises(ValueError, match="설문을 찾을 수 없습니다"):
            survey_commands.add_question(
                survey_id="nonexistent_id",
                text="테스트 질문",
                question_type="text"
            )

    def test_invalid_question_type(self, survey_commands):
        """잘못된 질문 유형으로 질문 추가 시 에러가 발생하는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 설문 생성
            2. 잘못된 질문 유형으로 질문 추가 시도
            3. ValueError 발생 확인
        """
        survey_id = survey_commands.create_survey(
            title="에러 테스트",
            description="에러 케이스 확인"
        )

        with pytest.raises(ValueError):
            survey_commands.add_question(
                survey_id=survey_id,
                text="테스트 질문",
                question_type="invalid_type"
            )


class TestScenario05:
    """시나리오 5: CSV 영속성 테스트"""

    def test_data_persistence(self, survey_commands, temp_data_dir):
        """데이터가 CSV 파일에 올바르게 저장되고 조회되는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처
            temp_data_dir: 임시 데이터 디렉토리 픽스처

        시나리오:
            1. 설문 생성 및 질문 추가
            2. CSV 파일 존재 확인
            3. CSV 파일 내용 검증
            4. 응답 제출 후 CSV 파일 내용 재검증
        """
        survey_id = survey_commands.create_survey(
            title="영속성 테스트",
            description="CSV 저장 확인"
        )

        q1_id = survey_commands.add_question(
            survey_id=survey_id,
            text="테스트 질문",
            question_type="rating"
        )

        surveys_csv = temp_data_dir / "surveys.csv"
        questions_csv = temp_data_dir / "questions.csv"
        responses_csv = temp_data_dir / "responses.csv"

        assert surveys_csv.exists()
        assert questions_csv.exists()
        assert responses_csv.exists()

        with open(surveys_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["id"] == survey_id
            assert rows[0]["title"] == "영속성 테스트"

        with open(questions_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["id"] == q1_id
            assert rows[0]["survey_id"] == survey_id
            assert rows[0]["text"] == "테스트 질문"

        survey_commands.submit_response(
            survey_id=survey_id,
            respondent_id="test_patient",
            answers={q1_id: "5"}
        )

        with open(responses_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["survey_id"] == survey_id
            assert rows[0]["question_id"] == q1_id
            assert rows[0]["answer"] == "5"
            assert rows[0]["respondent_id"] == "test_patient"

    def test_multiple_surveys_persistence(self, survey_commands, temp_data_dir):
        """여러 설문이 CSV에 올바르게 저장되는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처
            temp_data_dir: 임시 데이터 디렉토리 픽스처

        시나리오:
            1. 3개의 설문 생성
            2. 각 설문에 질문 추가
            3. CSV 파일에 모든 데이터가 저장되었는지 확인
            4. 설문 목록 조회로 검증
        """
        survey_ids = []
        for i in range(3):
            survey_id = survey_commands.create_survey(
                title=f"설문 {i+1}",
                description=f"테스트 설문 {i+1}"
            )
            survey_ids.append(survey_id)

            survey_commands.add_question(
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type="text"
            )

        surveys_csv = temp_data_dir / "surveys.csv"
        with open(surveys_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

        all_surveys = survey_commands.list_surveys()
        assert len(all_surveys) == 3
        stored_ids = [s["id"] for s in all_surveys]
        for survey_id in survey_ids:
            assert survey_id in stored_ids
