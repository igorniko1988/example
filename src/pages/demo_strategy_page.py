import random
import re
import time

import allure
from playwright.sync_api import Page, expect

from src.utils.allure_helpers import attach_expected_actual, attach_input_payload


class DemoStrategyPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open_demo_strategy_form(self) -> None:
        with allure.step("Open the My Strategies page"):
            self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)

        with allure.step("Open the Demo Trading tab"):
            demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
            expect(demo_tab).to_be_visible(timeout=30_000)
            demo_tab.click()

        with allure.step("Click Create Demo Strategy"):
            create_demo_button = self.page.get_by_role(
                "button", name=re.compile(r"Create Demo Strategy", re.I)
            ).first
            expect(create_demo_button).to_be_visible(timeout=30_000)
            create_demo_button.click()

        with allure.step("Verify the Create Demo Strategy page is open"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/create-demo"), timeout=30_000)
            expect(self.page.get_by_role("heading", name="Create Demo Strategy")).to_be_visible(timeout=30_000)

    def fill_required_demo_form_fields(self, strategy_name: str) -> None:
        with allure.step(f"Enter strategy name: {strategy_name}"):
            name_input = self.page.locator("input:not([type='hidden'])").first
            expect(name_input).to_be_visible(timeout=30_000)
            name_input.fill(strategy_name)
            attach_input_payload({"strategy_name": strategy_name})

        with allure.step("Select trading pair BTC/USDT"):
            pair_combo = self.page.get_by_role("combobox").first
            expect(pair_combo).to_be_visible(timeout=30_000)
            clicked = False
            for _ in range(6):
                aria_disabled = (pair_combo.get_attribute("aria-disabled") or "").lower()
                if aria_disabled == "true":
                    self.page.wait_for_timeout(800)
                    continue
                try:
                    pair_combo.scroll_into_view_if_needed()
                    pair_combo.click(timeout=3_000)
                    clicked = True
                    break
                except Exception:
                    try:
                        pair_combo.click(timeout=3_000, force=True)
                        clicked = True
                        break
                    except Exception:
                        self.page.wait_for_timeout(500)
            if not clicked:
                allure.attach(
                    "Pair combobox could not be clicked reliably. Proceeding with current/default pair.",
                    "pair_combobox_click_warning",
                    allure.attachment_type.TEXT,
                )
            else:
                self.page.keyboard.type("BTC/USDT")
                self.page.keyboard.press("Enter")
            attach_input_payload({"trading_pair": "BTC/USDT"})

        with allure.step("Set all amount fields from 10 to 1000"):
            visible_inputs = self.page.locator("input:not([type='hidden'])")
            changed = 0
            for idx in range(visible_inputs.count()):
                field = visible_inputs.nth(idx)
                if field.input_value().strip() == "10":
                    field.fill("1000")
                    changed += 1
            assert changed >= 2, "Expected at least two amount fields changed from 10 to 1000."
            self.page.keyboard.press("Tab")
            attach_input_payload({"amount_value_set": "1000"})
            attach_expected_actual("changed fields >= 2", f"changed fields: {changed}")

    def save_and_start_strategy(self) -> tuple[list[str], float | None]:
        save_start_button = self.page.get_by_role(
            "button", name=re.compile(r"Save and Start trading", re.I)
        ).first
        expect(save_start_button).to_be_enabled(timeout=30_000)
        observed_notifications: list[str] = []
        first_click_ts: float | None = None

        for _ in range(5):
            # Close potential open dropdowns/popovers before submit click.
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
            try:
                save_start_button.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                save_start_button.click()
            except Exception:
                save_start_button.click(force=True)
            if first_click_ts is None:
                first_click_ts = time.monotonic()
            self.page.wait_for_timeout(3000)
            observed_notifications.extend(self._collect_visible_notification_texts())

            error_dialog = self.page.locator("[role='dialog']").filter(has_text=re.compile(r"Error", re.I)).first
            if error_dialog.count() > 0 and error_dialog.is_visible():
                ok_btn = error_dialog.get_by_role("button", name=re.compile(r"^OK$", re.I))
                if ok_btn.count() > 0 and ok_btn.first.is_visible():
                    ok_btn.first.click()

            if re.search(r"/dashboard/bot/\d+/", self.page.url):
                deduped, seen = [], set()
                for text in observed_notifications:
                    if text not in seen:
                        seen.add(text)
                        deduped.append(text)
                elapsed = (time.monotonic() - first_click_ts) if first_click_ts is not None else None
                return deduped, elapsed

            # Futures form may reject low amounts (<100). Auto-correct and retry.
            if re.search(r"/dashboard/bot/create-futures", self.page.url):
                try:
                    # Re-open submit button state after potential validation popovers.
                    try:
                        self.page.keyboard.press("Escape")
                    except Exception:
                        pass
                    numeric_inputs = self.page.locator("input:not([type='hidden'])")
                    for idx in range(numeric_inputs.count()):
                        field = numeric_inputs.nth(idx)
                        if not field.is_visible():
                            continue
                        value = field.input_value().strip().replace(",", ".")
                        if not value:
                            continue
                        try:
                            if float(value) < 100:
                                field.fill("1000")
                        except ValueError:
                            continue
                    self.page.keyboard.press("Tab")
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass

        expect(self.page).to_have_url(re.compile(r"/dashboard/bot/\d+/"), timeout=30_000)
        elapsed = (time.monotonic() - first_click_ts) if first_click_ts is not None else None
        return observed_notifications, elapsed

    def assert_strategy_details_page_opened(self) -> str | None:
        with allure.step("Verify the strategy details page is open"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/\d+/"), timeout=30_000)
            expect(self.page.get_by_role("heading", name=re.compile(r"Strategy ID \d+"))).to_be_visible(timeout=30_000)
            attach_expected_actual(
                "URL matches /dashboard/bot/<id>/ and Strategy ID heading is visible",
                f"actual URL: {self.page.url}",
            )
            match = re.search(r"/dashboard/bot/(\d+)/?", self.page.url)
            return match.group(1) if match else None

    def click_strategy_action_button(self, label_pattern: str, action_name: str) -> float:
        with allure.step(f"Click '{action_name}' on the strategy details page"):
            self.dismiss_ok_dialogs_if_present()
            action_btn = self.page.get_by_role("button", name=re.compile(label_pattern, re.I)).first
            expect(action_btn).to_be_visible(timeout=30_000)
            action_click_ts = time.monotonic()
            action_btn.click()
            attach_input_payload({"action": f"click {action_name}"})
            return action_click_ts

    def click_start_deal(self) -> float:
        return self.click_strategy_action_button(r"start\s*deal", "Start deal")

    def click_close_deal(self) -> float:
        return self.click_strategy_action_button(r"close\s*deal", "Close deal")

    def click_stop_strategy(self) -> float:
        return self.click_strategy_action_button(r"^Stop", "Stop strategy")

    def confirm_start_with_market_price(self) -> None:
        with allure.step("Confirm Start Deal with market price"):
            market_dialog = self.page.get_by_role("dialog").filter(
                has_text=re.compile(r"start with market price|market price", re.I)
            ).first
            expect(market_dialog).to_be_visible(timeout=20_000)
            market_price_btn = market_dialog.get_by_role(
                "button", name=re.compile(r"start with market price", re.I)
            ).first
            expect(market_price_btn).to_be_visible(timeout=20_000)
            market_price_btn.click()

    def assert_front_notification(self, patterns: list[str], notification_name: str, timeout_sec: int = 20) -> str:
        deadline = time.time() + timeout_sec
        latest: list[str] = []
        regexes = [re.compile(pattern, re.I) for pattern in patterns]
        while time.time() < deadline:
            latest = self._collect_visible_notification_texts()
            for text in latest:
                if any(rx.search(text) for rx in regexes):
                    return text
            self.page.wait_for_timeout(500)
        allure.attach(
            "\n\n---\n\n".join(latest) if latest else "No visible notification texts found",
            f"{notification_name}_notification_debug",
            allure.attachment_type.TEXT,
        )
        raise AssertionError(f"Expected {notification_name} notification was not found. Expected patterns: {patterns}")

    def wait_for_front_event(
        self,
        event_name: str,
        state: str,
        timeout_sec: int = 180,
        fallback_patterns: list[str] | None = None,
        refresh_every_sec: int | None = None,
    ) -> str:
        event_pattern = r"[_\s\-]*".join(re.escape(part) for part in event_name.split("_"))
        regexes = [re.compile(rf"{event_pattern}.*{re.escape(state)}", re.I | re.S)]
        alias_patterns: dict[tuple[str, str], list[str]] = {
            ("strategy", "activated"): [r"has been activated", r"strategy has been created", r"trading log is ready"],
            ("start_order", "opened"): [
                r"placed the start order",
                r"start order.*placed",
                r"the start order has been placed",
                r"start order has been placed",
            ],
            ("start_order", "closed"): [
                r"start order was executed",
                r"start order.*executed",
                r"the start order has been executed",
                r"start order has been executed",
            ],
            ("close_position_order", "opened"): [
                r"deal closing order has been placed",
                r"the deal closing order has been placed",
                r"d\d+:\s*the deal closing order has been placed\.",
                r"d\d+:\s*the deal closing order has been placed",
                r"close position order has been placed",
            ],
            ("close_position_order", "closed"): [
                r"deal closing order has been executed",
                r"the deal closing order has been executed",
                r"d\d+:\s*the deal closing order has been executed\.",
                r"d\d+:\s*the deal closing order has been executed",
                r"close position order has been executed",
            ],
            ("deal", "completed"): [
                r"the deal was completed",
                r"deal profit is",
                r"total profit is",
                r"daily profit is",
            ],
        }
        for alias in alias_patterns.get((event_name, state), []):
            regexes.append(re.compile(alias, re.I))
        fallback_regexes = [re.compile(pattern, re.I) for pattern in (fallback_patterns or [])]

        end_time = time.time() + timeout_sec
        next_refresh_at = time.time() + refresh_every_sec if refresh_every_sec else None
        last_logs = ""
        while time.time() < end_time:
            logs_text = self._strategy_trading_logs_text()
            if any(rx.search(logs_text) for rx in regexes):
                return f"{event_name} {state}"
            if fallback_regexes and any(rx.search(logs_text) for rx in fallback_regexes):
                return f"{event_name} {state} (fallback)"
            last_logs = logs_text
            if next_refresh_at and time.time() >= next_refresh_at:
                allure.attach(
                    f"Refreshing page while waiting for '{event_name} {state}'",
                    f"{event_name}_{state}_auto_refresh",
                    allure.attachment_type.TEXT,
                )
                self.page.reload(wait_until="domcontentloaded")
                next_refresh_at = time.time() + refresh_every_sec
            self.page.wait_for_timeout(1000)
        allure.attach(last_logs[:8000], f"{event_name}_{state}_debug", allure.attachment_type.TEXT)
        raise AssertionError(f"Expected Strategy Trading Logs event '{event_name} {state}' was not found.")

    def wait_for_trading_logs_patterns(
        self,
        patterns: list[str],
        timeout_sec: int = 120,
        refresh_every_sec: int | None = None,
        debug_name: str = "trading_logs",
    ) -> str:
        regexes = [re.compile(pattern, re.I) for pattern in patterns]
        end_time = time.time() + timeout_sec
        next_refresh_at = time.time() + refresh_every_sec if refresh_every_sec else None
        last_logs = ""

        while time.time() < end_time:
            logs_text = self._strategy_trading_logs_text()
            if any(rx.search(logs_text) for rx in regexes):
                return logs_text
            last_logs = logs_text
            if next_refresh_at and time.time() >= next_refresh_at:
                self.page.reload(wait_until="domcontentloaded")
                next_refresh_at = time.time() + refresh_every_sec
            self.page.wait_for_timeout(1000)

        allure.attach(last_logs[:8000], f"{debug_name}_debug", allure.attachment_type.TEXT)
        raise AssertionError(f"Expected trading logs pattern was not found. Patterns: {patterns}")

    def dismiss_ok_dialogs_if_present(self, max_clicks: int = 6) -> int:
        clicked = 0
        for _ in range(max_clicks):
            ok_button = self.page.get_by_role("button", name=re.compile(r"^OK$", re.I)).first
            if ok_button.count() == 0:
                break
            try:
                if ok_button.is_visible(timeout=1_000):
                    ok_button.click(timeout=3_000)
                    clicked += 1
                    self.page.wait_for_timeout(400)
                    continue
            except Exception:
                break
            break
        return clicked

    def assert_strategy_popup_and_click_ok(self, patterns: list[str], popup_name: str, required: bool = True) -> str:
        dialog = self.page.get_by_role("dialog", name="Strategy")
        if required:
            expect(dialog).to_be_visible(timeout=60_000)
        else:
            try:
                expect(dialog).to_be_visible(timeout=8_000)
            except AssertionError:
                return ""
        text = dialog.inner_text()
        if not any(re.search(pattern, text, re.I) for pattern in patterns):
            allure.attach(text, f"{popup_name}_popup_debug", allure.attachment_type.TEXT)
            raise AssertionError(f"Unexpected '{popup_name}' popup text. Expected patterns: {patterns}")
        dialog.get_by_role("button", name="OK").click()
        return text

    def assert_confirmation_dialog_and_click_yes(self, title_pattern: str, text_patterns: list[str], dialog_name: str) -> str:
        dialog = self.page.get_by_role("dialog", name=re.compile(title_pattern, re.I))
        expect(dialog).to_be_visible(timeout=30_000)
        text = dialog.inner_text()
        if not any(re.search(pattern, text, re.I) for pattern in text_patterns):
            allure.attach(text, f"{dialog_name}_dialog_debug", allure.attachment_type.TEXT)
            raise AssertionError(f"Unexpected '{dialog_name}' dialog text. Expected patterns: {text_patterns}")
        dialog.get_by_role("button", name=re.compile(r"^yes$", re.I)).click()
        return text

    def assert_confirmation_dialog_and_click_yes_if_visible(
        self, title_pattern: str, text_patterns: list[str], dialog_name: str, timeout_ms: int = 8_000
    ) -> str:
        dialog = self.page.get_by_role("dialog", name=re.compile(title_pattern, re.I))
        try:
            expect(dialog).to_be_visible(timeout=timeout_ms)
        except AssertionError:
            return ""
        return self.assert_confirmation_dialog_and_click_yes(title_pattern, text_patterns, dialog_name)

    def delete_demo_strategy_from_list(self, strategy_name: str) -> None:
        self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
        demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
        expect(demo_tab).to_be_visible(timeout=30_000)
        demo_tab.click()

        strategy_card = self.page.locator(
            "xpath=//*[contains(@class, 'bot-card-demo') and .//*[normalize-space(text())="
            f"'{strategy_name}']]"
        ).first
        expect(strategy_card).to_be_visible(timeout=30_000)

        delete_button_candidates = [
            strategy_card.locator(".bot-card-demo__delete-strategy").first,
            strategy_card.locator("[class*='delete-strategy']").first,
            strategy_card.get_by_role("button", name=re.compile(r"delete|remove", re.I)).first,
        ]
        clicked = False
        for candidate in delete_button_candidates:
            if candidate.count() == 0:
                continue
            try:
                candidate.scroll_into_view_if_needed()
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
            raise AssertionError(f"Could not click delete button for strategy '{strategy_name}'.")

        delete_dialog = self.page.get_by_role("dialog", name=re.compile(r"Delete strategy", re.I))
        expect(delete_dialog).to_be_visible(timeout=30_000)

        confirm_candidates = [
            delete_dialog.get_by_role("button", name=re.compile(r"^Delete$", re.I)).first,
            delete_dialog.get_by_role("button", name=re.compile(r"^Yes$", re.I)).first,
            delete_dialog.get_by_role("button", name=re.compile(r"^OK$", re.I)).first,
            delete_dialog.get_by_role("button", name=re.compile(r"confirm|delete", re.I)).first,
            delete_dialog.locator("button").filter(has_text=re.compile(r"delete|yes|ok|confirm", re.I)).first,
        ]
        clicked = False
        for candidate in confirm_candidates:
            if candidate.count() == 0:
                continue
            try:
                if candidate.is_visible(timeout=2_000):
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
            # Fallback for non-standard button markup inside delete dialog.
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
            clicked = bool(clicked_via_dom)
        if not clicked:
            raise AssertionError("Could not click confirm button in delete strategy dialog.")

        # Front may return "please finish active deal" for a short period after close flow.
        active_deal_blocker = self.page.get_by_role("dialog", name=re.compile(r"Delete strategy", re.I)).filter(
            has_text=re.compile(r"finish active deal", re.I)
        )
        if active_deal_blocker.count() > 0 and active_deal_blocker.first.is_visible(timeout=1_500):
            self.dismiss_ok_dialogs_if_present(max_clicks=2)
            raise AssertionError("Delete blocked by active deal: 'please finish active deal'.")

        expect(
            self.page.locator(
                "xpath=//*[contains(@class, 'bot-card-demo') and .//*[normalize-space(text())="
                f"'{strategy_name}']]"
            )
        ).to_have_count(0, timeout=60_000)

    def delete_demo_strategy_from_list_if_exists(self, strategy_name: str) -> bool:
        self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)

        demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
        expect(demo_tab).to_be_visible(timeout=30_000)
        demo_tab.click()

        strategy_locator = self.page.locator(
            "xpath=//*[contains(@class, 'bot-card-demo') and .//*[normalize-space(text())="
            f"'{strategy_name}']]"
        )
        if strategy_locator.count() == 0:
            allure.attach(
                f"Strategy '{strategy_name}' was not found in demo list during cleanup.",
                "cleanup_strategy_not_found",
                allure.attachment_type.TEXT,
            )
            return False

        for attempt in range(6):
            try:
                self.delete_demo_strategy_from_list(strategy_name)
                return True
            except Exception as error:
                allure.attach(
                    f"Cleanup delete attempt {attempt + 1} failed: {error}",
                    f"cleanup_delete_attempt_{attempt + 1}",
                    allure.attachment_type.TEXT,
                )
                self.dismiss_ok_dialogs_if_present(max_clicks=3)
                self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
                self.page.wait_for_timeout(4_000)
        raise AssertionError(f"Failed to delete strategy '{strategy_name}' during cleanup.")

    def purge_test_demo_strategies(self, name_pattern: str = r"^d\d{5}$", max_delete: int = 30) -> int:
        self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
        demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
        expect(demo_tab).to_be_visible(timeout=30_000)
        demo_tab.click()
        self.page.wait_for_timeout(1200)

        name_rx = re.compile(name_pattern)
        deleted = 0
        for _ in range(max_delete):
            cards = self.page.locator("xpath=//*[contains(@class, 'bot-card-demo')]")
            card_count = cards.count()
            if card_count == 0:
                break

            target_name = ""
            for i in range(card_count):
                text = cards.nth(i).inner_text().strip()
                match = name_rx.search(text)
                if match:
                    target_name = match.group(0)
                    break

            if not target_name:
                break

            try:
                self.delete_demo_strategy_from_list(target_name)
                deleted += 1
            except Exception as error:
                allure.attach(
                    f"Purge delete failed for '{target_name}': {error}",
                    "purge_delete_error",
                    allure.attachment_type.TEXT,
                )
                self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
                demo_tab = self.page.get_by_role("tab", name=re.compile(r"Demo trading", re.I)).first
                if demo_tab.count() > 0:
                    demo_tab.click()
                self.page.wait_for_timeout(1000)
                continue

        allure.attach(str(deleted), "purged_test_demo_strategies_count", allure.attachment_type.TEXT)
        return deleted

    def _collect_visible_notification_texts(self) -> list[str]:
        selectors = ["[role='dialog']", "[role='alert']", "[class*='notification']", "[class*='toast']", "[class*='message']"]
        texts: list[str] = []
        for selector in selectors:
            locator = self.page.locator(selector)
            for idx in range(locator.count()):
                node = locator.nth(idx)
                try:
                    if node.is_visible(timeout=250):
                        raw = node.inner_text(timeout=750).strip()
                        if raw:
                            texts.append(raw)
                except Exception:
                    continue
        seen, unique = set(), []
        for text in texts:
            if text not in seen:
                seen.add(text)
                unique.append(text)
        return unique

    def _strategy_trading_logs_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        marker = "strategy trading logs"
        lower = body_text.lower()
        start_idx = lower.find(marker)
        if start_idx == -1:
            return body_text
        logs_text = body_text[start_idx:]
        for tail in ("Need help? Contact support", "Terms and Privacy Policy", "©"):
            tail_idx = logs_text.find(tail)
            if tail_idx != -1:
                logs_text = logs_text[:tail_idx]
                break
        return logs_text

    @staticmethod
    def _matching_log_lines(logs_text: str, regexes: list[re.Pattern[str]]) -> list[str]:
        lines = [line.strip() for line in logs_text.splitlines() if line.strip()]
        matched = [line for line in lines if any(rx.search(line) for rx in regexes)]
        seen, unique = set(), []
        for line in matched:
            if line not in seen:
                seen.add(line)
                unique.append(line)
        return unique

    @staticmethod
    def generate_strategy_name() -> str:
        return f"d{random.randint(10000, 99999)}"
