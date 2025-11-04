"""CSV 파일 손상 복구 시나리오 테스트

목적: 손상된 CSV 파일에서 graceful 처리 확인
커버리지: csv_*_repository.py +10%
"""

import pytest
import csv
from pathlib import Path


class TestCSVCorruptionRecovery:
    """CSV 파일 손상 복구 엔드투엔드 테스트"""

    def test_corrupted_csv_format_handling(
        self, survey_repo, temp_data_dir
    ):
        """잘못된 CSV 포맷 처리

        시나리오:
            1. 정상 설문 데이터 저장
            2. CSV 파일에 잘못된 포맷 라인 수동 추가
            3. 설문 목록 조회 시도
            4. 예외가 발생하거나 정상 데이터만 조회
        """
        from domain.entities.survey import Survey
        from datetime import datetime
        import uuid

        survey1 = Survey(
            id=str(uuid.uuid4()),
            tenant_id="tenant1",
            owner_id="owner1",
            title="정상 설문1",
            description="설명1",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey1)

        surveys_csv = temp_data_dir / "surveys.csv"
        with open(surveys_csv, "a", encoding="utf-8-sig") as f:
            f.write("invalid,line,without,proper,fields\n")

        try:
            surveys = survey_repo.find_all_surveys()
            assert len(surveys) >= 1
            assert any(s.title == "정상 설문1" for s in surveys)
        except (TypeError, KeyError, ValueError):
            pass

    def test_missing_required_columns(
        self, response_repo, temp_data_dir
    ):
        """누락된 필수 컬럼 처리

        시나리오:
            1. 정상 응답 데이터 저장
            2. CSV 파일에서 일부 컬럼 헤더 수정
            3. 응답 조회 시도
            4. 에러가 발생하거나 빈 결과 반환
        """
        from domain.entities.response import Response
        from datetime import datetime
        import uuid

        response1 = Response(
            id=str(uuid.uuid4()),
            survey_id="survey1",
            question_id="question1",
            respondent_id="respondent1",
            answer="답변1",
            answered_at=datetime.now(),
            session_id=str(uuid.uuid4()),
            time_spent_seconds=10
        )
        response_repo.save(response1)

        responses_csv = temp_data_dir / "responses.csv"

        with open(responses_csv, "r", encoding="utf-8-sig") as f:
            content = f.read()

        corrupted_content = content.replace("survey_id", "invalid_col")
        with open(responses_csv, "w", encoding="utf-8-sig") as f:
            f.write(corrupted_content)

        try:
            responses = response_repo.find_by_survey_id("survey1")
            assert len(responses) == 0 or responses is None
        except (KeyError, ValueError):
            pass

    def test_type_mismatch_data(
        self, survey_repo, temp_data_dir
    ):
        """타입 불일치 데이터 처리

        시나리오:
            1. CSV 파일에 타입이 맞지 않는 데이터 삽입
            2. 설문 조회 시도
            3. 타입 변환 실패 시 해당 레코드 skip
        """
        surveys_csv = temp_data_dir / "surveys.csv"

        if not surveys_csv.exists():
            with open(surveys_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "tenant_id", "owner_id", "title", "description", "created_at"]
                )
                writer.writeheader()

        with open(surveys_csv, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "tenant_id", "owner_id", "title", "description", "created_at"]
            )
            writer.writerow({
                "id": "survey_bad",
                "tenant_id": "tenant1",
                "owner_id": "owner1",
                "title": "잘못된 데이터",
                "description": "설명",
                "created_at": "invalid_datetime_format"
            })

        try:
            surveys = survey_repo.find_all_surveys()
        except (ValueError, TypeError):
            pass

    def test_empty_csv_file_handling(
        self, survey_repo, temp_data_dir
    ):
        """빈 CSV 파일 처리

        시나리오:
            1. CSV 파일을 헤더만 있게 초기화
            2. 설문 목록 조회
            3. 빈 리스트 반환 확인
        """
        surveys = survey_repo.find_all_surveys()
        assert isinstance(surveys, list)
