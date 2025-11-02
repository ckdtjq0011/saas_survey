"""CLI 메뉴 빌더 유틸리티

목적: 도메인별로 정리된 메뉴 구조를 쉽게 생성하고 관리
"""

from dataclasses import dataclass
from typing import Callable
from domain.entities.user import User


@dataclass(frozen=True, slots=True)
class MenuItem:
    """메뉴 아이템

    Attributes:
        key: 메뉴 선택 키 (예: "1", "2")
        label: 메뉴 레이블 (예: "설문 생성")
        description: 메뉴 설명
        handler: 메뉴 선택 시 실행될 핸들러 함수
        permission_check: 권한 체크 함수 (None이면 모든 사용자 접근 가능)
    """
    key: str
    label: str
    description: str
    handler: Callable | None = None
    permission_check: Callable[[User], bool] | None = None


class MenuBuilder:
    """메뉴 빌더

    도메인별로 메뉴를 그룹핑하고, 권한에 따라 필터링하여 메뉴를 생성합니다.
    """

    def __init__(self):
        """메뉴 빌더를 초기화합니다."""
        self.items: list[MenuItem] = []

    def add_item(
        self,
        label: str,
        description: str,
        handler: Callable | None = None,
        permission_check: Callable[[User], bool] | None = None
    ) -> None:
        """메뉴 아이템을 추가합니다.

        Args:
            label: 메뉴 레이블
            description: 메뉴 설명
            handler: 핸들러 함수
            permission_check: 권한 체크 함수
        """
        item = MenuItem(
            key="",
            label=label,
            description=description,
            handler=handler,
            permission_check=permission_check
        )
        self.items.append(item)

    def build(self, user: User | None = None) -> list[tuple[str, str, str]]:
        """사용자 권한에 따라 메뉴를 빌드합니다.

        Args:
            user: 사용자 엔티티 (None이면 모든 메뉴 표시)

        Returns:
            (key, label, description) 튜플 리스트
        """
        filtered_items = []

        for item in self.items:
            if item.permission_check is None:
                filtered_items.append(item)
            elif user and item.permission_check(user):
                filtered_items.append(item)

        result = []
        for idx, item in enumerate(filtered_items, 1):
            result.append((str(idx), item.label, item.description))

        return result

    def build_with_handlers(
        self, user: User | None = None
    ) -> dict[str, Callable]:
        """핸들러 매핑을 포함한 메뉴를 빌드합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            key → handler 매핑 딕셔너리
        """
        filtered_items = []

        for item in self.items:
            if item.permission_check is None:
                filtered_items.append(item)
            elif user and item.permission_check(user):
                filtered_items.append(item)

        handlers = {}
        for idx, item in enumerate(filtered_items, 1):
            if item.handler:
                handlers[str(idx)] = item.handler

        return handlers

    def clear(self) -> None:
        """메뉴 아이템을 모두 제거합니다."""
        self.items.clear()
