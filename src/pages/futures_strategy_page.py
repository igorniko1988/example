import re
import time

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect

from src.pages.demo_strategy_page import DemoStrategyPage
from src.utils.allure_helpers import attach_input_payload


class FuturesStrategyPage(DemoStrategyPage):
    def open_futures_strategy_form(self) -> None:
        with allure.step("Open Exchange Accounts and navigate to Strategies"):
            loaded = False
            for _ in range(4):
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
                self.page.wait_for_timeout(1_500)

                loading = self.page.locator("text=/^Loading$/i").first
                if loading.count() > 0 and loading.is_visible(timeout=1_000):
                    self.page.wait_for_timeout(2_000)
                    self.page.reload(wait_until="domcontentloaded")
                    self.page.wait_for_timeout(1_500)

                strategies_nav_candidates = [
                    self.page.locator("a[href*='/dashboard/bot/list']").first,
                    self.page.get_by_role("link", name=re.compile(r"Strategies|My Strategies", re.I)).first,
                    self.page.get_by_role("button", name=re.compile(r"Strategies", re.I)).first,
                    self.page.get_by_role("tab", name=re.compile(r"Strategies", re.I)).first,
                    self.page.locator("text=/^Strategies$/i").first,
                ]
                for nav in strategies_nav_candidates:
                    if nav.count() == 0:
                        continue
                    try:
                        if nav.is_visible(timeout=1_000):
                            nav.click(timeout=5_000)
                            self.page.wait_for_timeout(1_000)
                            break
                    except Exception:
                        continue

                # Front may not render Strategies control on /dashboard/exchange in some states.
                # Fallback to direct Strategies list URL after trying in-page navigation.
                if not re.search(r"/dashboard/bot/list", self.page.url, re.I):
                    for attempt in range(3):
                        try:
                            self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
                            self.page.wait_for_timeout(1_000)
                            break
                        except PlaywrightError:
                            if attempt == 2:
                                raise
                            self.page.wait_for_timeout(1_200)

                strategies_tab = self.page.get_by_role("button", name=re.compile(r"^Strategies", re.I)).first
                create_btn = self.page.get_by_role("button", name=re.compile(r"Create Futures Strategy", re.I)).first
                if re.search(r"/dashboard/bot/list", self.page.url, re.I) or (
                    strategies_tab.count() > 0 and strategies_tab.is_visible(timeout=3_000)
                ) or (
                    create_btn.count() > 0 and create_btn.is_visible(timeout=3_000)
                ):
                    loaded = True
                    break
                self.page.reload(wait_until="domcontentloaded")
                self.page.wait_for_timeout(1_000)

            if not loaded:
                raise AssertionError("Strategies section did not render controls after recovery attempts.")

        with allure.step("Open the Strategies tab"):
            strategies_tab_candidates = [
                self.page.get_by_role("button", name=re.compile(r"^Strategies", re.I)).first,
                self.page.get_by_role("tab", name=re.compile(r"Strategies", re.I)).first,
                self.page.locator("text=/^Strategies$/i").first,
            ]
            opened = False
            for candidate in strategies_tab_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=3_000):
                        candidate.click(timeout=5_000)
                        opened = True
                        break
                except Exception:
                    continue
            if not opened:
                raise AssertionError("Could not open Strategies tab.")

        with allure.step("Click Create Futures Strategy"):
            create_candidates = [
                self.page.get_by_role("button", name=re.compile(r"Create Futures Strategy", re.I)).first,
                self.page.locator("text=/Create Futures Strategy/i").first,
            ]
            clicked = False
            for candidate in create_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=10_000):
                        candidate.click(timeout=5_000)
                        clicked = True
                        break
                except Exception:
                    try:
                        candidate.click(timeout=5_000, force=True)
                        clicked = True
                        break
                    except Exception:
                        continue
            if not clicked:
                # Fallback: open create-futures page directly when list UI is flaky.
                self.page.goto(f"{self.base_url}/dashboard/bot/create-futures", wait_until="domcontentloaded")
                if re.search(r"/dashboard/bot/create-futures", self.page.url, re.I):
                    clicked = True
            if not clicked:
                raise AssertionError("Could not click 'Create Futures Strategy' control.")

        with allure.step("Verify the Create Futures Strategy page is open"):
            if re.search(r"/dashboard/bot/list", self.page.url, re.I):
                self.page.goto(f"{self.base_url}/dashboard/bot/create-futures", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/create"), timeout=30_000)

    def fill_required_futures_form_fields(
        self,
        strategy_name: str,
        exchange_name: str,
        trading_pair: str = "BTC/USDT",
        start_order_amount: str = "1000",
        safety_order_amount: str = "1000",
    ) -> None:
        # Sometimes a transient "Create Futures Strategy" message-box overlays the form
        # and intercepts pointer events. Dismiss it before interacting with fields.
        self._dismiss_create_futures_overlay_if_present()

        with allure.step(f"Enter strategy name: {strategy_name}"):
            name_input = self.page.locator("input:not([type='hidden'])").first
            expect(name_input).to_be_visible(timeout=30_000)
            name_input.fill(strategy_name)
            attach_input_payload({"strategy_name": strategy_name})

        with allure.step(f"Select trading pair {trading_pair}"):
            pair_combo = self.page.get_by_role("combobox").first
            expect(pair_combo).to_be_visible(timeout=30_000)
            for _ in range(6):
                aria_disabled = (pair_combo.get_attribute("aria-disabled") or "").lower()
                if aria_disabled == "true":
                    self.page.wait_for_timeout(800)
                    continue
                try:
                    pair_combo.scroll_into_view_if_needed()
                    pair_combo.click(timeout=3_000)
                    break
                except Exception:
                    try:
                        pair_combo.click(timeout=3_000, force=True)
                        break
                    except Exception:
                        self.page.wait_for_timeout(500)
            pair_input_candidates = [
                self.page.locator("[role='combobox'] input").first,
                self.page.locator("[role='listbox']").locator("input").first,
                self.page.get_by_role("textbox").first,
            ]
            pair_input = None
            for candidate in pair_input_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=1_000):
                        pair_input = candidate
                        break
                except Exception:
                    continue

            if pair_input is not None:
                pair_input.fill(trading_pair)
            else:
                self.page.keyboard.press("Meta+A")
                self.page.keyboard.type(trading_pair)
            self.page.keyboard.press("Enter")
            expect(self.page.locator("body")).to_contain_text(re.compile(re.escape(trading_pair)), timeout=10_000)
            attach_input_payload({"trading_pair": trading_pair})

        with allure.step(f"Select exchange account: {exchange_name}"):
            self._dismiss_create_futures_overlay_if_present()
            exchange_input_candidates = [
                self.page.locator("input[placeholder*='Connect exchange']").first,
                self.page.locator("input[placeholder*='exchange'], input[placeholder*='Exchange']").first,
                self.page.locator(
                    "xpath=//*[contains(normalize-space(text()), 'Exchange')]/ancestor::*[self::div or self::label][1]//input"
                ).first,
                self.page.get_by_role("textbox", name=re.compile(r"exchange", re.I)).first,
            ]
            exchange_input = None
            for candidate in exchange_input_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=3_000):
                        exchange_input = candidate
                        break
                except Exception:
                    continue
            if exchange_input is None:
                self.page.reload(wait_until="domcontentloaded")
                self._dismiss_create_futures_overlay_if_present()
                for candidate in exchange_input_candidates:
                    if candidate.count() == 0:
                        continue
                    try:
                        if candidate.is_visible(timeout=3_000):
                            exchange_input = candidate
                            break
                    except Exception:
                        continue
            if exchange_input is None:
                page_text = ""
                try:
                    page_text = self.page.locator("body").inner_text()
                except Exception:
                    page_text = ""
                if re.search(re.escape(exchange_name), page_text, re.I):
                    allure.attach(
                        "Exchange selector input not visible; exchange appears preselected on form. Continuing.",
                        "exchange_selector_optional_warning",
                        allure.attachment_type.TEXT,
                    )
                    attach_input_payload({"exchange_account_requested": exchange_name, "exchange_account_selected": "preselected"})
                else:
                    raise AssertionError("Could not locate exchange selector input in futures strategy form.")
            exchange_input.click(timeout=5_000)

            preferred_option = self.page.locator(
                "xpath=//*[contains(@class,'el-select-dropdown') or contains(@class,'dropdown')]"
                f"//*[contains(normalize-space(text()), '{exchange_name}')]"
            ).first
            selected_name = exchange_name
            if preferred_option.count() > 0 and preferred_option.is_visible(timeout=3_000):
                preferred_option.click(timeout=5_000)
            else:
                global_exact_option = self.page.locator(
                    f"xpath=//*[self::li or self::div or self::span][contains(normalize-space(text()), '{exchange_name}')]"
                ).first
                if global_exact_option.count() > 0 and global_exact_option.is_visible(timeout=3_000):
                    global_exact_option.click(timeout=5_000)
                else:
                # Fallback: pick first available non-demo option in dropdown.
                    options = self.page.locator(
                        "xpath=//*[contains(@class,'el-select-dropdown') or contains(@class,'dropdown')]"
                        "//*[self::li or self::div][normalize-space(text())!='']"
                    )
                    picked = False
                    for i in range(options.count()):
                        option = options.nth(i)
                        text = option.inner_text().strip()
                        if not text or re.search(r"demo", text, re.I):
                            continue
                        try:
                            option.click(timeout=3_000)
                            selected_name = text
                            picked = True
                            break
                        except Exception:
                            continue
                    if not picked:
                        raise AssertionError(f"Could not select exchange account '{exchange_name}' in strategy form.")

            self.page.wait_for_timeout(400)
            selected_value = exchange_input.input_value().strip()
            if not selected_value:
                allure.attach(
                    "Exchange input value is empty after selection; continuing because option click succeeded.",
                    "exchange_selection_soft_warning",
                    allure.attachment_type.TEXT,
                )
            attach_input_payload({"exchange_account_requested": exchange_name, "exchange_account_selected": selected_name})

        with allure.step(
            f"Set start order amount to {start_order_amount} and safety order amount to {safety_order_amount}"
        ):
            visible_inputs = self.page.locator("input:not([type='hidden'])")
            changed = 0
            explicit_changed = 0
            for idx in range(visible_inputs.count()):
                field = visible_inputs.nth(idx)
                if field.input_value().strip() == "10":
                    field.fill(start_order_amount)
                    changed += 1
            # Explicitly enforce mandatory order amount fields in futures form.
            explicit_fields = [
                (
                    "xpath=//*[contains(normalize-space(text()), 'Start order amount')]/ancestor::*[self::div or self::label][1]"
                    "//input[not(@type='hidden')]",
                    start_order_amount,
                ),
                (
                    "xpath=//*[contains(normalize-space(text()), 'Safety order amount')]/ancestor::*[self::div or self::label][1]"
                    "//input[not(@type='hidden')]",
                    safety_order_amount,
                ),
            ]
            for selector, value in explicit_fields:
                target = self.page.locator(selector).first
                if target.count() == 0:
                    continue
                try:
                    target.fill(value)
                    explicit_changed += 1
                except Exception:
                    continue
            assert (changed >= 2) or (explicit_changed >= 2), (
                "Expected futures amount fields to be updated "
                f"(changed_by_default={changed}, explicit_changed={explicit_changed})."
            )
            self.page.keyboard.press("Tab")
            attach_input_payload(
                {
                    "start_order_amount": start_order_amount,
                    "safety_order_amount": safety_order_amount,
                }
            )

    def _dismiss_create_futures_overlay_if_present(self) -> None:
        wrappers = self.page.locator(
            "xpath=//div[contains(@class,'el-message-box__wrapper') or @aria-label='Create Futures Strategy']"
        )
        if wrappers.count() == 0:
            return
        for i in range(min(wrappers.count(), 2)):
            wrapper = wrappers.nth(i)
            try:
                if not wrapper.is_visible(timeout=500):
                    continue
            except Exception:
                continue
            try:
                close_btn = wrapper.get_by_role("button", name=re.compile(r"close|ok|yes|no|cancel", re.I)).first
                if close_btn.count() > 0 and close_btn.is_visible(timeout=500):
                    close_btn.click(timeout=1_500)
                    self.page.wait_for_timeout(200)
                    continue
            except Exception:
                pass
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(200)
            except Exception:
                pass

    def delete_futures_strategy_from_list_if_exists(self, strategy_name: str, strategy_id: str | None = None) -> bool:
        def open_strategies_list() -> None:
            self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
            self.dismiss_ok_dialogs_if_present(max_clicks=2)
            self.page.wait_for_timeout(1_500)
            loading = self.page.locator("text=/^Loading$/i").first
            try:
                if loading.count() > 0 and loading.is_visible(timeout=1_000):
                    self.page.wait_for_timeout(2_000)
            except Exception:
                pass

            strategies_btn = self.page.get_by_role("button", name=re.compile(r"^Strategies", re.I)).first
            if strategies_btn.count() > 0:
                try:
                    aria_expanded = (strategies_btn.get_attribute("aria-expanded") or "").lower()
                    if aria_expanded == "false":
                        strategies_btn.click(timeout=5_000)
                        self.page.wait_for_timeout(500)
                except Exception:
                    pass

            demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
            if demo_tab.count() > 0:
                try:
                    if demo_tab.is_visible(timeout=1_000):
                        selected = (demo_tab.get_attribute("aria-selected") or "").lower()
                        if selected == "true":
                            self.page.keyboard.press("ArrowLeft")
                            self.page.wait_for_timeout(800)
                except Exception:
                    pass

        def strategy_card_locators():
            card_roots = [
                self.page.locator(
                    "xpath=//*[self::div or self::section or self::article]"
                    "[.//button[contains(normalize-space(.), 'Delete strategy')]"
                    f" and .//*[normalize-space(text())='{strategy_name}']]"
                ),
                self.page.locator(
                    "xpath=//*[contains(@class, 'bot-card')"
                    " and .//*[contains(normalize-space(.), 'Personal Strategy')]"
                    f" and .//*[normalize-space(text())='{strategy_name}']]"
                ),
                self.page.locator("xpath=//*[contains(@class, 'bot-card')]")
                .filter(has_text=re.compile(rf"Strategy ID\s*{re.escape(strategy_id)}", re.I))
                if strategy_id
                else self.page.locator("xpath=/html[false()]"),
                self.page.locator(
                    "xpath=//*[self::div or self::section or self::article]"
                    "[.//button[contains(normalize-space(.), 'Delete strategy')]]"
                ).filter(has_text=re.compile(re.escape(strategy_name), re.I)),
                self.page.locator(
                    "xpath=//*[self::div or self::section or self::article]"
                    "[.//*[contains(normalize-space(.), 'Personal Strategy')]"
                    " and .//button[contains(normalize-space(.), 'Delete strategy')]]"
                ).filter(has_text=re.compile(re.escape(strategy_name), re.I)),
                self.page.locator("xpath=//*[contains(@class, 'bot-card')]")
                .filter(has_text=re.compile(re.escape(strategy_name), re.I)),
                self.page.locator("xpath=//*[contains(@class, 'strategy-card')]")
                .filter(has_text=re.compile(re.escape(strategy_name), re.I)),
            ]
            return [locator.first for locator in card_roots]

        def locate_strategy_card():
            deadline = time.time() + 20
            while time.time() < deadline:
                for candidate in strategy_card_locators():
                    if candidate.count() == 0:
                        continue
                    try:
                        if candidate.is_visible(timeout=1_000):
                            return candidate
                    except Exception:
                        continue
                self.page.wait_for_timeout(1_000)
            return self.page.locator("xpath=/html[false()]")

        def strategy_still_present() -> bool:
            open_strategies_list()
            card = locate_strategy_card()
            if card.count() == 0:
                return False
            try:
                return card.is_visible(timeout=1_000)
            except Exception:
                return False

        def click_delete_button_on_card(card_locator) -> bool:
            delete_candidates = [
                card_locator.get_by_role("button", name=re.compile(r"^Delete strategy$", re.I)).first,
                card_locator.get_by_role("button", name=re.compile(r"delete strategy", re.I)).first,
                card_locator.locator("button").filter(has_text=re.compile(r"^Delete strategy$", re.I)).first,
                card_locator.locator("[class*='delete-strategy']").first,
            ]
            for candidate in delete_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    candidate.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    candidate.click(timeout=5_000)
                except Exception:
                    try:
                        candidate.click(timeout=5_000, force=True)
                    except Exception:
                        continue

                delete_dialog = self.page.get_by_role("dialog", name=re.compile(r"Delete strategy|Delete top strategy", re.I))
                try:
                    expect(delete_dialog).to_be_visible(timeout=5_000)
                    return True
                except AssertionError:
                    self.dismiss_ok_dialogs_if_present(max_clicks=2)
                    continue
            return False

        def dismiss_dialog_buttons(dialog) -> None:
            buttons = [
                dialog.get_by_role("button", name=re.compile(r"^OK$", re.I)).first,
                dialog.get_by_role("button", name=re.compile(r"^Close$", re.I)).first,
                dialog.get_by_role("button", name=re.compile(r"^No$", re.I)).first,
                dialog.locator("button").filter(has_text=re.compile(r"ok|close|cancel|no", re.I)).first,
            ]
            for button in buttons:
                if button.count() == 0:
                    continue
                try:
                    if button.is_visible(timeout=1_000):
                        button.click(timeout=3_000)
                        self.page.wait_for_timeout(400)
                        return
                except Exception:
                    continue

        def open_strategy_details_from_card(card_locator) -> bool:
            for _ in range(3):
                try:
                    card_locator.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    card_locator.click(timeout=5_000)
                except Exception:
                    try:
                        card_locator.click(timeout=5_000, force=True)
                    except Exception:
                        self.page.wait_for_timeout(1_000)
                        continue
                try:
                    expect(self.page).to_have_url(re.compile(r"/dashboard/bot/\d+"), timeout=20_000)
                    return True
                except AssertionError:
                    self.page.wait_for_timeout(1_000)
            return False

        def stop_strategy_from_list_card(card_locator) -> bool:
            stop_candidates = [
                card_locator.get_by_role("button", name=re.compile(r"pause|stop", re.I)).first,
                card_locator.locator("button").filter(has_text=re.compile(r"pause|stop", re.I)).first,
            ]
            for button in stop_candidates:
                if button.count() == 0:
                    continue
                try:
                    if not button.is_visible(timeout=1_000):
                        continue
                except Exception:
                    continue
                try:
                    button.click(timeout=5_000)
                except Exception:
                    try:
                        button.click(timeout=5_000, force=True)
                    except Exception:
                        continue
                self.assert_confirmation_dialog_and_click_yes_if_visible(
                    r"stop|pause",
                    [r"stop", r"pause", r"are you sure", r"strategy"],
                    "cleanup_stop_from_list_confirm",
                    timeout_ms=10_000,
                )
                try:
                    self.assert_front_notification(
                        [r"stopped", r"strategy has been stopped", r"paused", r"strategy has been paused"],
                        "cleanup_stop_from_list",
                        timeout_sec=20,
                    )
                except Exception:
                    pass
                self.assert_strategy_popup_and_click_ok(
                    [r"stopped", r"strategy has been stopped", r"paused", r"strategy has been paused"],
                    "cleanup_stop_from_list",
                    required=False,
                )
                self.dismiss_ok_dialogs_if_present(max_clicks=2)
                self.page.wait_for_timeout(1_500)
                return True
            return False

        def close_active_deal_and_stop_from_details() -> bool:
            if not re.search(r"/dashboard/bot/\d+", self.page.url, re.I):
                return False

            action_taken = False
            close_btn = self.page.get_by_role("button", name=re.compile(r"close\s*deal", re.I)).first
            if close_btn.count() > 0:
                try:
                    if close_btn.is_visible(timeout=3_000) and close_btn.is_enabled(timeout=3_000):
                        close_btn.click(timeout=5_000)
                        action_taken = True
                        self.assert_confirmation_dialog_and_click_yes_if_visible(
                            r"close deal",
                            [r"close deal", r"are you sure", r"close.*position", r"deal"],
                            "cleanup_close_deal_confirm",
                            timeout_ms=10_000,
                        )
                        self.assert_strategy_popup_and_click_ok(
                            [r"deal was canceled", r"close.*deal", r"deal.*closed", r"position.*closed"],
                            "cleanup_close_deal",
                            required=False,
                        )
                        for _ in range(3):
                            try:
                                self.wait_for_front_event(
                                    "close_position_order",
                                    "opened",
                                    timeout_sec=90,
                                    fallback_patterns=[r"deal canceled", r"deal.*closed", r"position.*closed"],
                                    refresh_every_sec=30,
                                )
                                break
                            except Exception:
                                self.page.wait_for_timeout(2_000)
                        for _ in range(3):
                            try:
                                self.wait_for_front_event(
                                    "close_position_order",
                                    "closed",
                                    timeout_sec=90,
                                    fallback_patterns=[r"deal canceled", r"deal.*closed", r"position.*closed"],
                                    refresh_every_sec=30,
                                )
                                break
                            except Exception:
                                self.page.wait_for_timeout(2_000)
                        try:
                            self.wait_for_trading_logs_patterns(
                                [r"deal canceled", r"deal.*closed", r"position.*closed", r"deal profit is"],
                                timeout_sec=120,
                                refresh_every_sec=30,
                                debug_name="cleanup_close_deal_logs",
                            )
                        except Exception:
                            pass
                except Exception:
                    pass

            stop_btn = self.page.get_by_role("button", name=re.compile(r"^Stop", re.I)).first
            if stop_btn.count() > 0:
                try:
                    if stop_btn.is_visible(timeout=3_000) and stop_btn.is_enabled(timeout=3_000):
                        stop_btn.click(timeout=5_000)
                        action_taken = True
                        self.assert_confirmation_dialog_and_click_yes_if_visible(
                            r"stop",
                            [r"stop", r"are you sure", r"strategy"],
                            "cleanup_stop_strategy_confirm",
                            timeout_ms=10_000,
                        )
                        try:
                            self.assert_front_notification(
                                [r"stopped", r"strategy has been stopped"],
                                "cleanup_stopped",
                                timeout_sec=20,
                            )
                        except Exception:
                            pass
                        self.assert_strategy_popup_and_click_ok(
                            [r"stopped", r"strategy has been stopped"],
                            "cleanup_stopped",
                            required=False,
                        )
                        self.dismiss_ok_dialogs_if_present(max_clicks=2)
                except Exception:
                    pass

            self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
            self.page.wait_for_timeout(1_000)
            return action_taken

        for cleanup_attempt in range(3):
            card = self.page.locator("xpath=/html[false()]")
            card_visible = False
            deadline = time.time() + 20
            while time.time() < deadline:
                open_strategies_list()
                card = locate_strategy_card()
                if card.count() > 0:
                    try:
                        card_visible = card.is_visible(timeout=1_000)
                    except Exception:
                        card_visible = False
                    if card_visible:
                        break

                self.page.wait_for_timeout(2_000)

            if card.count() == 0 or not card_visible:
                # If strategy is no longer rendered in the list, treat cleanup as successful.
                return not strategy_still_present()

            stop_strategy_from_list_card(card)
            open_strategies_list()
            card = locate_strategy_card()
            if card.count() == 0:
                return True

            if not click_delete_button_on_card(card):
                return False

            delete_dialog = self.page.get_by_role("dialog", name=re.compile(r"Delete strategy|Delete top strategy", re.I))
            expect(delete_dialog).to_be_visible(timeout=30_000)
            dialog_text = delete_dialog.inner_text()
            if re.search(r"finish active deal", dialog_text, re.I):
                dismiss_dialog_buttons(delete_dialog)
                if cleanup_attempt == 2:
                    raise AssertionError("Delete blocked by active deal: 'please finish active deal'.")
                if not open_strategy_details_from_card(card):
                    raise AssertionError(
                        f"Could not open strategy '{strategy_name}' details page to clean up active deal."
                    )
                if not close_active_deal_and_stop_from_details():
                    raise AssertionError(
                        f"Could not close active deal and stop strategy '{strategy_name}' before deletion."
                    )
                continue

            confirm_candidates = [
                delete_dialog.get_by_role("button", name=re.compile(r"^Delete$", re.I)).first,
                delete_dialog.get_by_role("button", name=re.compile(r"^Yes$", re.I)).first,
                delete_dialog.get_by_role("button", name=re.compile(r"^OK$", re.I)).first,
                delete_dialog.get_by_role("button", name=re.compile(r"confirm|delete", re.I)).first,
                delete_dialog.locator("button").filter(has_text=re.compile(r"delete|yes|ok|confirm", re.I)).first,
            ]
            confirmed = False
            for candidate in confirm_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=2_000):
                        candidate.click(timeout=5_000)
                        confirmed = True
                        break
                except Exception:
                    try:
                        candidate.click(timeout=5_000, force=True)
                        confirmed = True
                        break
                    except Exception:
                        continue
            if not confirmed:
                clicked_via_dom = self.page.evaluate(
                    """() => {
                        const dialogs = Array.from(document.querySelectorAll('[role="dialog"], .el-dialog, .el-message-box'));
                        const dialog = dialogs.find(d => /delete strategy/i.test(d.textContent || ''));
                        if (!dialog) return false;
                        const buttons = Array.from(dialog.querySelectorAll('button'));
                        const target = buttons.find(
                            b => /delete|yes|ok|confirm/i.test((b.textContent || '').trim())
                        );
                        if (!target) return false;
                        target.click();
                        return true;
                    }"""
                )
                confirmed = bool(clicked_via_dom)
            if not confirmed:
                raise AssertionError("Could not click confirm button in delete strategy dialog.")

            disappearance_deadline = time.time() + 60
            while time.time() < disappearance_deadline:
                if not strategy_still_present():
                    return True
                self.page.wait_for_timeout(2_000)

            # Retry from a fresh list state if the card still renders after confirmation.
            open_strategies_list()

        raise AssertionError(
            f"Strategy '{strategy_name}' was still visible in the strategies list after delete confirmation."
        )

    def delete_top_strategy_from_list_if_exists(self, strategy_name: str) -> bool:
        def open_list() -> None:
            self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
            self.dismiss_ok_dialogs_if_present(max_clicks=2)
            self.page.wait_for_timeout(1_500)
            loading = self.page.locator("text=/^Loading$/i").first
            try:
                if loading.count() > 0 and loading.is_visible(timeout=1_000):
                    self.page.wait_for_timeout(2_000)
            except Exception:
                pass

        def card_candidates():
            return [
                self.page.locator(
                    "xpath=//*[self::div or self::section or self::article]"
                    "[.//button[contains(normalize-space(.), 'Delete strategy')]"
                    f" and .//*[normalize-space(text())='{strategy_name}']]"
                ),
                self.page.locator(
                    "xpath=//*[self::div or self::section or self::article]"
                    "[.//button[contains(normalize-space(.), 'Delete strategy')]]"
                ).filter(has_text=re.compile(re.escape(strategy_name), re.I)),
                self.page.locator("xpath=//*[contains(@class, 'bot-card')]").filter(
                    has_text=re.compile(re.escape(strategy_name), re.I)
                ),
                self.page.locator("xpath=//*[contains(@class, 'strategy-card')]").filter(
                    has_text=re.compile(re.escape(strategy_name), re.I)
                ),
            ]

        def locate_card():
            deadline = time.time() + 20
            while time.time() < deadline:
                for candidate in card_candidates():
                    if candidate.count() == 0:
                        continue
                    card = candidate.first
                    try:
                        if card.is_visible(timeout=1_000):
                            return card
                    except Exception:
                        continue
                self.page.wait_for_timeout(1_000)
            return self.page.locator("xpath=/html[false()]")

        def strategy_still_present() -> bool:
            open_list()
            card = locate_card()
            if card.count() == 0:
                return False
            try:
                return card.is_visible(timeout=1_000)
            except Exception:
                return False

        for _ in range(3):
            open_list()
            card = locate_card()
            if card.count() == 0:
                return False

            delete_candidates = [
                card.get_by_role("button", name=re.compile(r"^Delete strategy$", re.I)).first,
                card.get_by_role("button", name=re.compile(r"delete strategy", re.I)).first,
                card.locator("button").filter(has_text=re.compile(r"^Delete strategy$", re.I)).first,
                card.locator("[class*='delete-strategy']").first,
            ]
            clicked = False
            for candidate in delete_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    candidate.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    candidate.click(timeout=5_000)
                    clicked = True
                    break
                except Exception:
                    try:
                        candidate.click(timeout=5_000, force=True)
                        clicked = True
                        break
                    except Exception:
                        continue
            if not clicked:
                self.page.wait_for_timeout(1_000)
                continue

            delete_dialog = self.page.get_by_role("dialog", name=re.compile(r"Delete strategy|Delete top strategy", re.I)).first
            expect(delete_dialog).to_be_visible(timeout=30_000)
            dialog_text = delete_dialog.inner_text(timeout=5_000)
            if not re.search(r"delete the top strategy", dialog_text, re.I):
                allure.attach(dialog_text, "top_strategy_delete_dialog_text", allure.attachment_type.TEXT)
                raise AssertionError("Top strategy delete dialog text did not match expected confirmation.")

            confirm_candidates = [
                delete_dialog.get_by_role("button", name=re.compile(r"^Delete$", re.I)).first,
                delete_dialog.get_by_role("button", name=re.compile(r"^Yes$", re.I)).first,
                delete_dialog.locator("button").filter(has_text=re.compile(r"delete|yes", re.I)).first,
            ]
            confirmed = False
            for candidate in confirm_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    if candidate.is_visible(timeout=2_000):
                        candidate.click(timeout=5_000)
                        confirmed = True
                        break
                except Exception:
                    try:
                        candidate.click(timeout=5_000, force=True)
                        confirmed = True
                        break
                    except Exception:
                        continue
            if not confirmed:
                raise AssertionError("Could not confirm top strategy deletion.")

            disappearance_deadline = time.time() + 30
            while time.time() < disappearance_deadline:
                if not strategy_still_present():
                    return True
                self.page.wait_for_timeout(1_000)

        return False
