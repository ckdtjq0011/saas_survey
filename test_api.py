import logging
import requests
import json


logger = logging.getLogger(__name__)
BASE_URL = "http://localhost:8000"


def test_api() -> None:
    """API를 테스트합니다."""
    logger.info("=" * 60)
    logger.info("FastAPI 테스트 시작")
    logger.info("=" * 60)

    logger.info("\n1. 헬스 체크")
    response = requests.get(f"{BASE_URL}/health")
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {response.json()}")

    logger.info("\n2. 설문 생성")
    create_data = {
        "title": "API 테스트 설문",
        "description": "FastAPI를 통한 테스트입니다"
    }
    response = requests.post(f"{BASE_URL}/api/v1/surveys", json=create_data)
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {response.json()}")
    survey_id = response.json()["survey_id"]

    logger.info("\n3. 질문 추가 - 평점형")
    question_data = {
        "text": "서비스에 만족하십니까?",
        "question_type": "rating"
    }
    response = requests.post(f"{BASE_URL}/api/v1/surveys/{survey_id}/questions", json=question_data)
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {response.json()}")
    q1_id = response.json()["question_id"]

    logger.info("\n4. 질문 추가 - 객관식")
    question_data = {
        "text": "가장 좋았던 점은?",
        "question_type": "choice",
        "options": ["의료진", "시설", "대기시간"]
    }
    response = requests.post(f"{BASE_URL}/api/v1/surveys/{survey_id}/questions", json=question_data)
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {response.json()}")
    q2_id = response.json()["question_id"]

    logger.info("\n5. 설문 조회")
    response = requests.get(f"{BASE_URL}/api/v1/surveys/{survey_id}")
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    logger.info("\n6. 응답 제출")
    response_data = {
        "respondent_id": "patient_001",
        "answers": {
            q1_id: "5",
            q2_id: "의료진"
        }
    }
    response = requests.post(f"{BASE_URL}/api/v1/surveys/{survey_id}/responses", json=response_data)
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {response.json()}")

    logger.info("\n7. 결과 조회")
    response = requests.get(f"{BASE_URL}/api/v1/surveys/{survey_id}/results")
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    logger.info("\n8. 설문 목록 조회")
    response = requests.get(f"{BASE_URL}/api/v1/surveys")
    logger.info(f"   Status: {response.status_code}")
    logger.info(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    logger.info("\n" + "=" * 60)
    logger.info("모든 API 테스트 완료")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
