"""멀티테넌트 시나리오 통합 테스트입니다."""

import logging
from pathlib import Path
import shutil
from domain.value_objects.role import Role
from interface.cli.commands import Commands


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def setup_test_environment() -> Path:
    """테스트 환경을 초기화합니다."""
    test_data_dir = Path("test_data_multitenant")
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    test_data_dir.mkdir()
    return test_data_dir


def test_scenario_1_tenant_isolation(commands: Commands) -> None:
    """시나리오 1: 테넌트 격리 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("시나리오 1: 테넌트 격리 테스트")
    logger.info("=" * 60)

    logger.info("\n[1단계] 두 개의 테넌트 생성")
    tenant_a_id = commands.register_tenant("병원 A")
    tenant_b_id = commands.register_tenant("병원 B")
    logger.info(f"테넌트 A ID: {tenant_a_id}")
    logger.info(f"테넌트 B ID: {tenant_b_id}")

    logger.info("\n[2단계] 각 테넌트에 관리자 생성")
    success_a, admin_a_id = commands.register_user(
        tenant_a_id, "admin_a", "admin_a@hospital_a.com", "password123", "tenant_admin"
    )
    success_b, admin_b_id = commands.register_user(
        tenant_b_id, "admin_b", "admin_b@hospital_b.com", "password123", "tenant_admin"
    )
    assert success_a, f"테넌트 A 관리자 생성 실패: {admin_a_id}"
    assert success_b, f"테넌트 B 관리자 생성 실패: {admin_b_id}"
    logger.info(f"테넌트 A 관리자 ID: {admin_a_id}")
    logger.info(f"테넌트 B 관리자 ID: {admin_b_id}")

    logger.info("\n[3단계] 각 관리자 로그인")
    success_a, api_key_a, user_a = commands.login("admin_a", "password123", tenant_a_id)
    success_b, api_key_b, user_b = commands.login("admin_b", "password123", tenant_b_id)
    assert success_a and user_a, f"테넌트 A 관리자 로그인 실패: {api_key_a}"
    assert success_b and user_b, f"테넌트 B 관리자 로그인 실패: {api_key_b}"
    logger.info("두 관리자 모두 로그인 성공")

    logger.info("\n[4단계] 각 관리자가 설문 생성")
    success_a, survey_a_id = commands.create_survey(user_a, "병원 A 만족도 조사", "병원 A 전용 설문")
    success_b, survey_b_id = commands.create_survey(user_b, "병원 B 만족도 조사", "병원 B 전용 설문")
    assert success_a, f"테넌트 A 설문 생성 실패: {survey_a_id}"
    assert success_b, f"테넌트 B 설문 생성 실패: {survey_b_id}"
    logger.info(f"테넌트 A 설문 ID: {survey_a_id}")
    logger.info(f"테넌트 B 설문 ID: {survey_b_id}")

    logger.info("\n[5단계] 테넌트 격리 검증")
    surveys_a = commands.list_surveys(user_a)
    surveys_b = commands.list_surveys(user_b)
    logger.info(f"테넌트 A가 볼 수 있는 설문 수: {len(surveys_a)}")
    logger.info(f"테넌트 B가 볼 수 있는 설문 수: {len(surveys_b)}")
    assert len(surveys_a) == 1, "테넌트 A는 자신의 설문 1개만 볼 수 있어야 함"
    assert len(surveys_b) == 1, "테넌트 B는 자신의 설문 1개만 볼 수 있어야 함"
    assert surveys_a[0]['id'] == survey_a_id, "테넌트 A는 자신의 설문만 조회해야 함"
    assert surveys_b[0]['id'] == survey_b_id, "테넌트 B는 자신의 설문만 조회해야 함"

    logger.info("\n[6단계] 크로스 테넌트 접근 차단 검증")
    success, error, _ = commands.get_survey(user_a, survey_b_id)
    assert not success, "테넌트 A는 테넌트 B의 설문에 접근할 수 없어야 함"
    logger.info(f"크로스 테넌트 접근 차단 확인: {error}")

    logger.info("\n[결과] 시나리오 1 통과: 테넌트 격리 정상 작동")


def test_scenario_2_role_permissions(commands: Commands) -> None:
    """시나리오 2: 역할별 권한 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("시나리오 2: 역할별 권한 테스트")
    logger.info("=" * 60)

    logger.info("\n[1단계] 테넌트 및 다양한 역할의 사용자 생성")
    tenant_id = commands.register_tenant("종합병원")
    logger.info(f"테넌트 ID: {tenant_id}")

    success_admin, admin_id = commands.register_user(
        tenant_id, "admin", "admin@hospital.com", "password123", "tenant_admin"
    )
    success_manager, manager_id = commands.register_user(
        tenant_id, "manager", "manager@hospital.com", "password123", "survey_manager"
    )
    success_resp, resp_id = commands.register_user(
        tenant_id, "respondent", "respondent@hospital.com", "password123", "respondent"
    )

    assert success_admin and success_manager and success_resp
    logger.info(f"관리자 ID: {admin_id}")
    logger.info(f"매니저 ID: {manager_id}")
    logger.info(f"응답자 ID: {resp_id}")

    logger.info("\n[2단계] 모든 사용자 로그인")
    _, _, admin = commands.login("admin", "password123", tenant_id)
    _, _, manager = commands.login("manager", "password123", tenant_id)
    _, _, respondent = commands.login("respondent", "password123", tenant_id)

    assert admin and manager and respondent
    logger.info("모든 사용자 로그인 성공")

    logger.info("\n[3단계] 설문 생성 권한 테스트")
    success_admin, survey_admin_id = commands.create_survey(admin, "관리자 설문", "관리자가 생성")
    success_manager, survey_manager_id = commands.create_survey(manager, "매니저 설문", "매니저가 생성")
    success_resp, error_resp = commands.create_survey(respondent, "응답자 설문", "응답자가 생성 시도")

    assert success_admin, "TENANT_ADMIN은 설문 생성 가능해야 함"
    assert success_manager, "SURVEY_MANAGER는 설문 생성 가능해야 함"
    assert not success_resp, "RESPONDENT는 설문 생성 불가해야 함"
    logger.info(f"관리자 설문 생성 성공: {survey_admin_id}")
    logger.info(f"매니저 설문 생성 성공: {survey_manager_id}")
    logger.info(f"응답자 설문 생성 차단: {error_resp}")

    logger.info("\n[4단계] 질문 추가 권한 테스트")
    success_admin, _ = commands.add_question(admin, survey_admin_id, "질문1", "text")
    success_manager, _ = commands.add_question(manager, survey_manager_id, "질문2", "text")
    success_resp, error = commands.add_question(respondent, survey_admin_id, "질문3", "text")

    assert success_admin, "관리자는 자신의 설문에 질문 추가 가능"
    assert success_manager, "매니저는 자신의 설문에 질문 추가 가능"
    assert not success_resp, "응답자는 질문 추가 불가"
    logger.info(f"응답자 질문 추가 차단: {error}")

    logger.info("\n[5단계] 결과 조회 권한 테스트")
    success_admin, _, _ = commands.get_results(admin, survey_admin_id)
    success_manager, _, _ = commands.get_results(manager, survey_manager_id)
    success_resp, error, _ = commands.get_results(respondent, survey_admin_id)

    assert success_admin, "관리자는 모든 결과 조회 가능"
    assert success_manager, "매니저는 자신의 설문 결과 조회 가능"
    assert not success_resp, "응답자는 결과 조회 불가"
    logger.info(f"응답자 결과 조회 차단: {error}")

    logger.info("\n[6단계] 응답 제출 권한 테스트")
    success, _ = commands.submit_response(respondent, survey_admin_id, {})
    assert success, "모든 역할이 응답 제출 가능해야 함"
    logger.info("응답자 응답 제출 성공")

    logger.info("\n[결과] 시나리오 2 통과: 역할별 권한 정상 작동")


def test_scenario_3_owner_vs_non_owner(commands: Commands) -> None:
    """시나리오 3: 소유자 vs 비소유자 권한 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("시나리오 3: 소유자 vs 비소유자 권한 테스트")
    logger.info("=" * 60)

    logger.info("\n[1단계] 테넌트 및 두 명의 매니저 생성")
    tenant_id = commands.register_tenant("대학병원")

    success_m1, _ = commands.register_user(tenant_id, "manager1", "m1@hospital.com", "password123", "survey_manager")
    success_m2, _ = commands.register_user(tenant_id, "manager2", "m2@hospital.com", "password123", "survey_manager")
    assert success_m1 and success_m2

    _, _, manager1 = commands.login("manager1", "password123", tenant_id)
    _, _, manager2 = commands.login("manager2", "password123", tenant_id)
    assert manager1 and manager2
    logger.info("두 매니저 로그인 성공")

    logger.info("\n[2단계] 매니저1이 설문 생성")
    success, survey_id = commands.create_survey(manager1, "매니저1 설문", "매니저1 소유")
    assert success
    logger.info(f"매니저1 설문 생성: {survey_id}")

    logger.info("\n[3단계] 소유자(매니저1) 권한 테스트")
    success, _ = commands.add_question(manager1, survey_id, "소유자 질문", "text")
    assert success, "소유자는 자신의 설문 관리 가능"
    logger.info("소유자 질문 추가 성공")

    success, _, _ = commands.get_results(manager1, survey_id)
    assert success, "소유자는 자신의 설문 결과 조회 가능"
    logger.info("소유자 결과 조회 성공")

    logger.info("\n[4단계] 비소유자(매니저2) 권한 테스트")
    success, error = commands.add_question(manager2, survey_id, "비소유자 질문", "text")
    assert not success, "SURVEY_MANAGER는 타인의 설문 관리 불가"
    logger.info(f"비소유자 질문 추가 차단: {error}")

    success, error, _ = commands.get_results(manager2, survey_id)
    assert not success, "SURVEY_MANAGER는 타인의 설문 결과 조회 불가"
    logger.info(f"비소유자 결과 조회 차단: {error}")

    logger.info("\n[5단계] TENANT_ADMIN은 모든 설문 관리 가능 확인")
    success_admin, _ = commands.register_user(tenant_id, "admin", "admin@hospital.com", "password123", "tenant_admin")
    _, _, admin = commands.login("admin", "password123", tenant_id)
    assert admin

    success, _ = commands.add_question(admin, survey_id, "관리자 질문", "text")
    assert success, "TENANT_ADMIN은 모든 설문 관리 가능"
    logger.info("TENANT_ADMIN이 타인 설문 관리 성공")

    success, _, _ = commands.get_results(admin, survey_id)
    assert success, "TENANT_ADMIN은 모든 설문 결과 조회 가능"
    logger.info("TENANT_ADMIN이 타인 설문 결과 조회 성공")

    logger.info("\n[결과] 시나리오 3 통과: 소유자/비소유자 권한 정상 작동")


def test_scenario_4_complete_workflow(commands: Commands) -> None:
    """시나리오 4: 완전한 워크플로우 통합 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("시나리오 4: 완전한 워크플로우 통합 테스트")
    logger.info("=" * 60)

    logger.info("\n[1단계] 병원 설립 (테넌트 등록)")
    tenant_id = commands.register_tenant("서울 중앙 병원")
    logger.info(f"병원 등록 완료: {tenant_id}")

    logger.info("\n[2단계] 관리자 입사 (사용자 등록)")
    success, admin_id = commands.register_user(
        tenant_id, "kim_admin", "kim@hospital.com", "admin2024", "tenant_admin"
    )
    assert success
    logger.info(f"관리자 등록 완료: {admin_id}")

    logger.info("\n[3단계] 관리자 출근 (로그인)")
    success, api_key, admin = commands.login("kim_admin", "admin2024", tenant_id)
    assert success and admin
    logger.info(f"관리자 로그인 성공")

    logger.info("\n[4단계] 만족도 설문 준비 (설문 생성)")
    success, survey_id = commands.create_survey(admin, "2024년 상반기 만족도 조사", "환자 만족도 조사")
    assert success
    logger.info(f"설문 생성 완료: {survey_id}")

    logger.info("\n[5단계] 설문 항목 작성 (질문 추가)")
    questions = [
        ("전반적인 만족도는?", "rating", None),
        ("가장 만족스러웠던 점은?", "choice", ["의료진", "시설", "대기시간"]),
        ("개선사항을 적어주세요", "text", None),
    ]

    for text, qtype, options in questions:
        success, qid = commands.add_question(admin, survey_id, text, qtype, options)
        assert success
        logger.info(f"질문 추가 완료: {text}")

    logger.info("\n[6단계] 환자 등록 (응답자 사용자 등록)")
    patients = []
    for i in range(3):
        success, pid = commands.register_user(
            tenant_id, f"patient{i+1}", f"patient{i+1}@gmail.com", "patient123", "respondent"
        )
        assert success
        _, _, patient = commands.login(f"patient{i+1}", "patient123", tenant_id)
        patients.append(patient)
    logger.info(f"환자 {len(patients)}명 등록 완료")

    logger.info("\n[7단계] 환자 설문 응답 (응답 제출)")
    success, _, survey_data = commands.get_survey(admin, survey_id)
    assert success and survey_data

    for idx, patient in enumerate(patients):
        answers = {}
        for q in survey_data['questions']:
            if q['type'] == 'rating':
                answers[q['id']] = str(4 + (idx % 2))
            elif q['type'] == 'choice':
                answers[q['id']] = q['options'][idx % len(q['options'])]
            else:
                answers[q['id']] = f"환자{idx+1}의 의견입니다"

        success, _ = commands.submit_response(patient, survey_id, answers)
        assert success
        logger.info(f"환자{idx+1} 응답 제출 완료")

    logger.info("\n[8단계] 결과 분석 (결과 조회)")
    success, _, results = commands.get_results(admin, survey_id)
    assert success and results
    logger.info(f"총 {len(results)}개 질문에 대한 결과 조회")

    for q_id, stats in results.items():
        logger.info(f"- {stats['question']}: {stats['count']}개 응답")
        if 'average' in stats:
            logger.info(f"  평균 평점: {stats['average']}")
        if 'distribution' in stats:
            logger.info(f"  분포: {stats['distribution']}")

    logger.info("\n[9단계] 관리자 퇴근 (로그아웃)")
    success = commands.logout(api_key)
    assert success
    logger.info("로그아웃 성공")

    logger.info("\n[결과] 시나리오 4 통과: 완전한 워크플로우 정상 작동")


def test_scenario_5_session_validation(commands: Commands) -> None:
    """시나리오 5: 세션 검증 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("시나리오 5: 세션 검증 테스트")
    logger.info("=" * 60)

    logger.info("\n[1단계] 테넌트 및 사용자 생성")
    tenant_id = commands.register_tenant("테스트 병원")
    success, _ = commands.register_user(tenant_id, "testuser", "test@test.com", "password123", "tenant_admin")
    assert success

    logger.info("\n[2단계] 로그인하여 API 키 획득")
    success, api_key, user = commands.login("testuser", "password123", tenant_id)
    assert success and user and api_key
    logger.info(f"로그인 성공, API 키 획득")

    logger.info("\n[3단계] API 키로 세션 검증")
    success, _, validated_user = commands.validate_session(api_key)
    assert success and validated_user
    assert validated_user.username == "testuser"
    logger.info("세션 검증 성공")

    logger.info("\n[4단계] 잘못된 API 키로 세션 검증")
    success, error, _ = commands.validate_session("invalid_api_key_123")
    assert not success
    logger.info(f"잘못된 API 키 검증 실패: {error}")

    logger.info("\n[5단계] 로그아웃 후 세션 검증")
    commands.logout(api_key)
    success, error, _ = commands.validate_session(api_key)
    assert not success
    logger.info(f"로그아웃된 세션 검증 실패: {error}")

    logger.info("\n[결과] 시나리오 5 통과: 세션 검증 정상 작동")


def main() -> None:
    """모든 멀티테넌트 시나리오 테스트를 실행합니다."""
    logger.info("\n" + "=" * 80)
    logger.info("멀티테넌트 SaaS 플랫폼 시나리오 테스트 시작")
    logger.info("=" * 80)

    test_data_dir = setup_test_environment()
    logger.info(f"\n테스트 데이터 디렉토리: {test_data_dir}")

    commands = Commands(test_data_dir)

    try:
        test_scenario_1_tenant_isolation(commands)
        test_scenario_2_role_permissions(commands)
        test_scenario_3_owner_vs_non_owner(commands)
        test_scenario_4_complete_workflow(commands)
        test_scenario_5_session_validation(commands)

        logger.info("\n" + "=" * 80)
        logger.info("모든 시나리오 테스트 통과!")
        logger.info("=" * 80)
        logger.info("\n테스트 결과:")
        logger.info("- 테넌트 격리: PASS")
        logger.info("- 역할별 권한: PASS")
        logger.info("- 소유자/비소유자 권한: PASS")
        logger.info("- 완전한 워크플로우: PASS")
        logger.info("- 세션 검증: PASS")
        logger.info("\n멀티테넌트 SaaS 플랫폼이 정상적으로 작동합니다.")

    except AssertionError as e:
        logger.error(f"\n테스트 실패: {e}")
        raise
    except Exception:
        logger.exception("\n테스트 중 오류 발생")
        raise
    finally:
        logger.info(f"\n테스트 데이터 정리: {test_data_dir}")
        if test_data_dir.exists():
            shutil.rmtree(test_data_dir)


if __name__ == "__main__":
    main()
