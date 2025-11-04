from domain.entities.user import User
from interface.cli.handlers.base_handler import BaseHandler


class CategoryHandler(BaseHandler):
    """범주 관리를 처리하는 Handler입니다."""

    def create_top_level_category_flow(self, user: User) -> None:
        """대범주 생성 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("대범주 생성")

            name = self.ui.get_input("범주 이름")
            if not name or not name.strip():
                self.ui.print_error("범주 이름은 필수입니다")
                return

            description = self.ui.get_input("범주 설명")
            if not description or not description.strip():
                self.ui.print_error("범주 설명은 필수입니다")
                return

            order_str = self.ui.get_input("표시 순서 (기본값: 0)")
            try:
                order = int(order_str) if order_str else 0
            except ValueError:
                self.ui.print_error("표시 순서는 숫자여야 합니다")
                return

            success, result = self.commands.create_category(
                user, name, description, None, order
            )

            if success:
                self.ui.print_success(f"대범주가 생성되었습니다. ID: {result}")
            else:
                self.ui.print_error(f"대범주 생성 실패: {result}")

        except Exception as e:
            self.handle_error("대범주 생성", e)
        finally:
            self.ui.pause()

    def create_subcategory_flow(self, user: User) -> None:
        """소범주 생성 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("소범주 생성")

            parent_id = self._select_top_level_category(user)
            if not parent_id:
                return

            name = self.ui.get_input("범주 이름")
            if not name or not name.strip():
                self.ui.print_error("범주 이름은 필수입니다")
                return

            description = self.ui.get_input("범주 설명")
            if not description or not description.strip():
                self.ui.print_error("범주 설명은 필수입니다")
                return

            order_str = self.ui.get_input("표시 순서 (기본값: 0)")
            try:
                order = int(order_str) if order_str else 0
            except ValueError:
                self.ui.print_error("표시 순서는 숫자여야 합니다")
                return

            success, result = self.commands.create_category(
                user, name, description, parent_id, order
            )

            if success:
                self.ui.print_success(f"소범주가 생성되었습니다. ID: {result}")
            else:
                self.ui.print_error(f"소범주 생성 실패: {result}")

        except Exception as e:
            self.handle_error("소범주 생성", e)
        finally:
            self.ui.pause()

    def list_categories_flow(self, user: User) -> None:
        """범주 목록 조회 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("범주 목록")

            success, result = self.commands.list_all_categories(user)

            if not success:
                self.ui.print_error(f"범주 목록 조회 실패: {result}")
                return

            categories = result

            if not categories:
                self.ui.print_info("범주가 없습니다")
                return

            top_level_categories = [c for c in categories if c.is_top_level()]
            top_level_categories.sort(key=lambda c: c.order)

            for top_cat in top_level_categories:
                self.ui.print_info(f"\n[대범주] {top_cat.name}")
                self.ui.print_info(f"  설명: {top_cat.description}")
                self.ui.print_info(f"  순서: {top_cat.order}")

                subcategories = [c for c in categories if c.parent_id == top_cat.id]
                subcategories.sort(key=lambda c: c.order)

                if subcategories:
                    for sub_cat in subcategories:
                        self.ui.print_info(f"  - [하위범주] {sub_cat.name}")
                        self.ui.print_info(f"    설명: {sub_cat.description}")
                        self.ui.print_info(f"    순서: {sub_cat.order}")

            standalone_subcategories = [c for c in categories if not c.is_top_level()]
            top_level_ids = [c.id for c in top_level_categories]
            orphan_subcategories = [c for c in standalone_subcategories if c.parent_id not in top_level_ids]

            if orphan_subcategories:
                self.ui.print_info("\n[기타 하위범주]")
                for sub_cat in orphan_subcategories:
                    self.ui.print_info(f"  - {sub_cat.name}")
                    self.ui.print_info(f"    설명: {sub_cat.description}")

        except Exception as e:
            self.handle_error("범주 목록 조회", e)
        finally:
            self.ui.pause()

    def update_category_flow(self, user: User) -> None:
        """범주 수정 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("범주 수정")

            category_id = self._select_category(user)
            if not category_id:
                return

            success, error, category_data = self.commands.get_category(user, category_id)
            if not success or not category_data:
                self.ui.print_error(f"범주 조회 실패: {error}")
                return

            self.ui.print_info(f"\n현재 범주 정보:")
            self.ui.print_info(f"이름: {category_data['name']}")
            self.ui.print_info(f"설명: {category_data['description']}")
            self.ui.print_info(f"순서: {category_data['order']}")
            self.ui.print_info(f"활성화: {category_data['is_active']}\n")

            choice = self.ui.get_choice(
                "수정할 항목을 선택하세요",
                choices=["이름", "설명", "순서", "활성화 상태", "취소"],
            )

            updates = {}

            if choice == "이름":
                new_name = self.ui.get_input("새 이름")
                if new_name and new_name.strip():
                    updates["name"] = new_name.strip()
            elif choice == "설명":
                new_description = self.ui.get_input("새 설명")
                if new_description and new_description.strip():
                    updates["description"] = new_description.strip()
            elif choice == "순서":
                new_order = self.ui.get_input("새 순서")
                try:
                    updates["order"] = int(new_order)
                except ValueError:
                    self.ui.print_error("순서는 숫자여야 합니다")
                    return
            elif choice == "활성화 상태":
                new_active = self.ui.get_choice(
                    "활성화 상태",
                    choices=["활성화", "비활성화"],
                )
                updates["is_active"] = new_active == "활성화"
            else:
                return

            if not updates:
                self.ui.print_info("수정 사항이 없습니다")
                return

            success, result = self.commands.update_category(user, category_id, **updates)

            if success:
                self.ui.print_success("범주가 수정되었습니다")
            else:
                self.ui.print_error(f"범주 수정 실패: {result}")

        except Exception as e:
            self.handle_error("범주 수정", e)
        finally:
            self.ui.pause()

    def delete_category_flow(self, user: User) -> None:
        """범주 삭제 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("범주 삭제")

            category_id = self._select_category(user)
            if not category_id:
                return

            success, error, category_data = self.commands.get_category(user, category_id)
            if not success or not category_data:
                self.ui.print_error(f"범주 조회 실패: {error}")
                return

            self.ui.print_info(f"\n삭제할 범주:")
            self.ui.print_info(f"이름: {category_data['name']}")
            self.ui.print_info(f"설명: {category_data['description']}\n")

            if not self.confirm(f"정말 '{category_data['name']}' 범주를 삭제하시겠습니까?"):
                self.ui.print_info("삭제가 취소되었습니다")
                return

            success, result = self.commands.delete_category(user, category_id)

            if success:
                self.ui.print_success("범주가 삭제되었습니다")
            else:
                self.ui.print_error(f"범주 삭제 실패: {result}")

        except Exception as e:
            self.handle_error("범주 삭제", e)
        finally:
            self.ui.pause()

    def _select_category(self, user: User) -> str | None:
        """범주를 선택합니다.

        Args:
            user: 현재 로그인한 사용자

        Returns:
            선택된 범주 ID, 취소 시 None
        """
        success, result = self.commands.list_all_categories(user)

        if not success:
            self.ui.print_error(f"범주 목록 조회 실패: {result}")
            return None

        categories = result

        if not categories:
            self.ui.print_info("범주가 없습니다")
            return None

        choices = []
        for cat in categories:
            if cat.is_top_level():
                choices.append(f"[대범주] {cat.name}")
            else:
                choices.append(f"  [하위범주] {cat.name}")

        selected_choice = self.ui.get_choice("범주 선택", choices=choices + ["취소"])

        if selected_choice == "취소":
            return None

        for cat in categories:
            if f"[대범주] {cat.name}" == selected_choice or f"  [하위범주] {cat.name}" == selected_choice:
                return cat.id

        return None

    def _select_top_level_category(self, user: User) -> str | None:
        """최상위 범주를 선택합니다.

        Args:
            user: 현재 로그인한 사용자

        Returns:
            선택된 범주 ID, 취소 시 None
        """
        success, result = self.commands.list_categories(user, parent_id=None)

        if not success:
            self.ui.print_error(f"범주 목록 조회 실패: {result}")
            return None

        categories = result

        if not categories:
            self.ui.print_info("최상위 범주가 없습니다")
            return None

        choices = [cat.name for cat in categories]

        selected_choice = self.ui.get_choice("상위 범주 선택", choices=choices + ["취소"])

        if selected_choice == "취소":
            return None

        for cat in categories:
            if cat.name == selected_choice:
                return cat.id

        return None
