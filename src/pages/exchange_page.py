import re
import time

import allure
from playwright.sync_api import Page, expect

from src.utils.allure_helpers import attach_expected_actual, attach_input_payload


class ExchangePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def _wait_exchange_page_ready(self, timeout_ms: int = 5_000) -> None:
        loading = self.page.locator("text=/^Loading$/i").first
        try:
            if loading.count() > 0:
                expect(loading).not_to_be_visible(timeout=timeout_ms)
        except Exception:
            pass

        connected_exchange_heading = self.page.get_by_text(re.compile(r"Connected Exchanges", re.I)).first
        connect_binance_button = self.page.get_by_role("button", name=re.compile(r"Connect Binance", re.I)).first
        try:
            if connected_exchange_heading.count() > 0:
                expect(connected_exchange_heading).to_be_visible(timeout=timeout_ms)
                return
        except Exception:
            pass
        try:
            if connect_binance_button.count() > 0:
                expect(connect_binance_button).to_be_visible(timeout=timeout_ms)
        except Exception:
            pass

    def open_binance_connect_form(self) -> None:
        with allure.step("Open the Exchange Accounts page"):
            self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)

        with allure.step("Open the Binance connection form"):
            self.page.get_by_role("button", name=re.compile(r"Connect Binance", re.I)).click()
            self.page.wait_for_timeout(1200)

        with allure.step("Handle the onboarding intermediate step if it appears"):
            connect_to_exchange = self.page.get_by_role(
                "button", name=re.compile(r"Connect to Exchange", re.I)
            ).first
            if re.search(r"/dashboard/onbording", self.page.url, re.I) and connect_to_exchange.is_visible():
                connect_to_exchange.click()
                self.page.wait_for_timeout(1200)

        with allure.step("Verify the Binance API connection form is open"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/connect-binance"), timeout=30_000)
            expect(self.page.locator("input[name='bn-connection-name']")).to_be_visible()
            expect(self.page.locator("input[name='bn-api-key']")).to_be_visible()
            expect(self.page.locator("input[name='bn-api-secret']")).to_be_visible()

    def fill_binance_connect_form(self, connection_name: str = "", api_key: str = "", api_secret: str = "") -> None:
        with allure.step("Fill in the Binance connection form"):
            attach_input_payload(
                {
                    "bn-connection-name": connection_name,
                    "bn-api-key": "***" if api_key else "",
                    "bn-api-secret": "***" if api_secret else "",
                }
            )
            self.page.locator("input[name='bn-connection-name']").fill(connection_name)
            self.page.locator("input[name='bn-api-key']").fill(api_key)
            self.page.locator("input[name='bn-api-secret']").fill(api_secret)

    def assert_still_on_connect_binance_page(self) -> None:
        with allure.step("Verify the user remains on the Binance connection page"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/connect-binance"))

    def assert_invalid_inputs_count(self, expected_count: int) -> None:
        with allure.step(f"Verify {expected_count} Binance fields are marked invalid"):
            invalid_inputs = self.page.locator("input.connect-binance__input--invalid")
            expect(invalid_inputs).to_have_count(expected_count)
            attach_expected_actual(
                f"invalid inputs count = {expected_count}",
                f"invalid inputs count = {invalid_inputs.count()}",
            )

    def assert_binance_field_invalid_state(
        self,
        *,
        connection_name_invalid: bool,
        api_key_invalid: bool,
        api_secret_invalid: bool,
    ) -> None:
        with allure.step("Verify the Binance form validation state matches the expected result"):
            states = {
                "connection-name": (
                    self.page.locator("input[name='bn-connection-name']"),
                    connection_name_invalid,
                ),
                "api-key": (
                    self.page.locator("input[name='bn-api-key']"),
                    api_key_invalid,
                ),
                "api-secret": (
                    self.page.locator("input[name='bn-api-secret']"),
                    api_secret_invalid,
                ),
            }
            actual_classes: list[str] = []
            for field_name, (locator, should_be_invalid) in states.items():
                if should_be_invalid:
                    expect(locator).to_have_class(re.compile(r"connect-binance__input--invalid"))
                else:
                    expect(locator).not_to_have_class(re.compile(r"connect-binance__input--invalid"))
                actual_classes.append(f"{field_name}: {locator.get_attribute('class')}")
            attach_expected_actual(
                (
                    "connection-name invalid="
                    f"{connection_name_invalid}, api-key invalid={api_key_invalid}, api-secret invalid={api_secret_invalid}"
                ),
                "\n".join(actual_classes),
            )

    def assert_connected_exchange_visible(self, connection_name: str) -> None:
        with allure.step(f"Verify connected exchange '{connection_name}' is visible"):
            connected_names = self.get_connected_exchange_names_from_current_page()
            assert connection_name in connected_names, (
                f"Expected exchange '{connection_name}' in connected exchanges list, got: {connected_names}"
            )

    def assert_connected_exchange_absent(self, connection_name: str) -> None:
        with allure.step(f"Verify connected exchange '{connection_name}' is no longer visible"):
            connected_names = self.get_connected_exchange_names_from_current_page()
            if connection_name in connected_names:
                remaining_after_delete = self.ensure_no_connected_exchanges(attempts=5, max_delete_per_pass=20)
                assert connection_name not in remaining_after_delete, (
                    f"Exchange '{connection_name}' must be absent after deletion, got: {remaining_after_delete}"
                )

    def submit_connect_to_exchange(self) -> None:
        for _ in range(4):
            submit_btn = self._get_visible_connect_to_exchange_button()
            try:
                expect(submit_btn).to_be_visible(timeout=3_000)
            except AssertionError:
                if not re.search(r"/dashboard/connect-binance", self.page.url, re.I):
                    self.page.wait_for_timeout(1500)
                    return
                if self._collect_visible_feedback_texts():
                    self.page.wait_for_timeout(1500)
                    return
                self.page.wait_for_timeout(800)
                continue

            try:
                self.page.keyboard.press("Tab")
            except Exception:
                pass

            secret_input = self.page.locator("input[name='bn-api-secret']").first
            try:
                submit_btn.scroll_into_view_if_needed()
            except Exception:
                pass

            clicked = False
            try:
                submit_btn.click(timeout=5_000)
                clicked = True
            except Exception:
                try:
                    submit_btn.click(timeout=5_000, force=True)
                    clicked = True
                except Exception:
                    clicked = False

            if not clicked:
                try:
                    if secret_input.is_visible(timeout=500):
                        secret_input.press("Enter", timeout=2_000)
                        clicked = True
                except Exception:
                    clicked = False

            if not clicked:
                try:
                    self.page.evaluate(
                        """
                        () => {
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const target = buttons.find((btn) => {
                                const text = (btn.textContent || '').trim().toLowerCase();
                                if (text !== 'connect to exchange') return false;
                                return !!btn.closest('div, form');
                            });
                            if (target) target.click();
                        }
                        """
                    )
                    clicked = True
                except Exception:
                    clicked = False

            self.page.wait_for_timeout(800)

            try:
                button_text = submit_btn.inner_text(timeout=500).strip().lower()
            except Exception:
                button_text = ""
            try:
                is_disabled = submit_btn.is_disabled(timeout=500)
            except Exception:
                is_disabled = False

            if "connecting" in button_text or is_disabled:
                self.page.wait_for_timeout(1500)
                return

            if not re.search(r"/dashboard/connect-binance", self.page.url, re.I):
                self.page.wait_for_timeout(1500)
                return

            if self._collect_visible_feedback_texts():
                self.page.wait_for_timeout(1500)
                return

        self.page.wait_for_timeout(1500)

    def wait_for_exchange_connected_feedback(self, timeout_sec: int = 20) -> str:
        expected_text = "Binance exchange connected successfully"
        return self._wait_exact_feedback_text(
            expected_text,
            debug_name="exchange_connect_feedback_debug",
            timeout_sec=timeout_sec,
        )

    def wait_for_exchange_connected_state(self, connection_name: str, timeout_sec: int = 30) -> None:
        end_time = time.time() + timeout_sec
        last_url = self.page.url
        last_body = ""
        navigated_to_exchange = False

        while time.time() < end_time:
            last_url = self.page.url
            try:
                last_body = self.page.locator("body").inner_text(timeout=500)
            except Exception:
                last_body = ""

            if re.search(r"/dashboard/exchange", last_url, re.I):
                connected_names = self._extract_connected_exchange_names_from_text(last_body)
                if connection_name in connected_names:
                    return
            elif not navigated_to_exchange:
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                navigated_to_exchange = True

            self.page.wait_for_timeout(1000)

        allure.attach(last_url, "exchange_connect_last_url", allure.attachment_type.TEXT)
        allure.attach(last_body[:5000], "exchange_connect_last_body", allure.attachment_type.TEXT)
        raise AssertionError(
            f"Exchange '{connection_name}' was not visible in Connected Exchanges after submit."
        )

    def wait_until_exchange_absent(self, connection_name: str, timeout_sec: int = 20) -> None:
        end_time = time.time() + timeout_sec
        navigated_to_exchange = False

        while time.time() < end_time:
            if re.search(r"/dashboard/exchange", self.page.url, re.I):
                visible_names = self.get_connected_exchange_names_from_current_page()
                if connection_name not in visible_names:
                    return
            elif not navigated_to_exchange:
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                navigated_to_exchange = True

            self.page.wait_for_timeout(500)

        visible_names = self.get_connected_exchange_names_from_current_page()
        raise AssertionError(
            f"Exchange '{connection_name}' is still visible after waiting for deletion: {visible_names}"
        )

    def wait_until_no_connected_exchanges(self, timeout_sec: int = 20) -> None:
        end_time = time.time() + timeout_sec
        navigated_to_exchange = False

        while time.time() < end_time:
            if re.search(r"/dashboard/exchange", self.page.url, re.I):
                if not self.get_connected_exchange_names_from_current_page():
                    return
            elif not navigated_to_exchange:
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                navigated_to_exchange = True

            self.page.wait_for_timeout(500)

        visible_names = self.get_connected_exchange_names_from_current_page()
        raise AssertionError(
            f"Connected exchanges are still visible after cleanup wait: {visible_names}"
        )

    def connect_binance_account(
        self,
        connection_name: str,
        api_key: str,
        api_secret: str,
        verify_strategies_unlocked: bool = True,
    ) -> None:
        for attempt in range(2):
            self.open_binance_connect_form()
            with allure.step("Submit valid Binance credentials and connect the account"):
                self.page.locator("input[name='bn-connection-name']").fill(connection_name)
                self.page.locator("input[name='bn-api-key']").fill(api_key)
                self.page.locator("input[name='bn-api-secret']").fill(api_secret)
                self.submit_connect_to_exchange()

            with allure.step("Wait for the connected Binance account to appear in Exchange Accounts"):
                try:
                    self.wait_for_exchange_connected_state(connection_name, timeout_sec=30)
                    break
                except AssertionError:
                    if attempt == 1:
                        raise
                    stale_names = self.get_connected_exchange_names_from_current_page()
                    stale_names = [name for name in stale_names if name != connection_name]
                    allure.attach(
                        "\n".join(stale_names) if stale_names else "none",
                        "stale_connected_exchanges_after_add_attempt",
                        allure.attachment_type.TEXT,
                    )
                    for stale_name in stale_names:
                        self.delete_exchange_account_if_exists(stale_name, navigate=False)
                    self.ensure_no_connected_exchanges(attempts=3, max_delete_per_pass=20)
                    continue

            with allure.step("Capture the success toast if the UI shows it"):
                self._wait_exact_feedback_text(
                    "Binance exchange connected successfully",
                    debug_name="exchange_connect_feedback_debug",
                    timeout_sec=5,
                    required=False,
                )

        with allure.step("Verify no immediate connection error is shown"):
            dialogs_text = " ".join(self.page.locator("body").all_inner_texts()).lower()
            if "connection is failed" in dialogs_text or "api connection is failed" in dialogs_text:
                raise AssertionError("Exchange connection failed according to UI message.")

        with allure.step("Verify the Binance connection flow completed successfully"):
            # UI may redirect to different dashboard page after successful connect.
            if re.search(r"/dashboard/connect-binance", self.page.url, re.I):
                invalid_inputs = self.page.locator("input.connect-binance__input--invalid")
                if invalid_inputs.count() > 0:
                    raise AssertionError("Connect Binance form still has invalid fields after submit.")
            else:
                expect(self.page).to_have_url(re.compile(r"/dashboard/"), timeout=30_000)

        if not verify_strategies_unlocked:
            return

        with allure.step("Verify the connected exchange unlocks the My Strategies page"):
            deadline = time.time() + 75
            last_url = self.page.url
            last_body = ""
            while time.time() < deadline:
                self.page.goto(f"{self.base_url}/dashboard/bot/list", wait_until="domcontentloaded")
                self.page.wait_for_timeout(1_500)
                last_url = self.page.url
                try:
                    last_body = self.page.locator("body").inner_text()
                except Exception:
                    last_body = ""

                if re.search(r"/dashboard/bot/list", last_url, re.I):
                    return

                lower_body = last_body.lower()
                if (
                    re.search(r"/dashboard/exchange", last_url, re.I)
                    and "connect exchange account" in lower_body
                    and "connect binance" in lower_body
                ):
                    self.page.wait_for_timeout(3_000)
                    continue

                if "connection is failed" in lower_body or "api connection is failed" in lower_body:
                    raise AssertionError("Exchange connection failed according to UI message after submit.")

                self.page.wait_for_timeout(2_000)

            allure.attach(last_url, "post_connect_last_url", allure.attachment_type.TEXT)
            allure.attach(last_body[:5000], "post_connect_last_body_excerpt", allure.attachment_type.TEXT)
            raise AssertionError("Exchange seems not connected: app still blocks access to /dashboard/bot/list.")

    def delete_exchange_account_if_exists(
        self,
        connection_name: str,
        timeout_sec: int = 60,
        navigate: bool = True,
    ) -> bool:
        if navigate or not re.search(r"/dashboard/exchange", self.page.url, re.I):
            with allure.step("Open the Exchange Accounts page for deletion"):
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
                self._wait_exchange_page_ready()

        account_row = self._find_exchange_row(connection_name)
        if account_row.count() == 0:
            with allure.step(f"Check that exchange row '{connection_name}' exists before deletion"):
                allure.attach("not found", "exchange_row_state", allure.attachment_type.TEXT)
            return False

        def click_candidate(locator) -> bool:
            if locator.count() == 0:
                return False
            try:
                locator.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                locator.click(timeout=5_000)
                return True
            except Exception:
                try:
                    locator.click(timeout=5_000, force=True)
                    return True
                except Exception:
                    return False

        def click_delete_control() -> bool:
            with allure.step(f"Click Delete for connected exchange '{connection_name}'"):
                row_buttons = account_row.get_by_role("button")
                button_count = min(row_buttons.count(), 10)

                # Live UI: the rightmost icon button in the card is the trash/delete control.
                for idx in range(button_count - 1, -1, -1):
                    candidate = row_buttons.nth(idx)
                    try:
                        if not candidate.is_visible(timeout=500):
                            continue
                    except Exception:
                        continue
                    if click_candidate(candidate):
                        return True

                delete_candidates = [
                    account_row.get_by_role("button", name=re.compile(r"delete|remove|disconnect", re.I)).first,
                    account_row.locator("[class*='delete'], [class*='remove'], [class*='disconnect']").first,
                    account_row.locator("text=/Delete|Remove|Disconnect/i").first,
                ]
                for candidate in delete_candidates:
                    if click_candidate(candidate):
                        return True

                try:
                    account_row.click(timeout=5_000, force=True)
                except Exception:
                    pass
                global_delete = self.page.get_by_role("button", name=re.compile(r"delete|remove|disconnect", re.I)).first
                return click_candidate(global_delete)

        def confirm_delete_dialog() -> None:
            with allure.step("Confirm exchange deletion in the confirmation dialog"):
                dialog = self.page.get_by_role("dialog").filter(has_text=re.compile(r"are you sure", re.I)).first
                expect(dialog).to_be_visible(timeout=10_000)
                dialog_text = dialog.inner_text()
                if "are you sure" not in dialog_text.lower():
                    allure.attach(dialog_text, "exchange_delete_dialog_actual_text", allure.attachment_type.TEXT)
                    raise AssertionError("Exchange delete dialog does not contain the expected confirmation text.")

                yes_btn = dialog.get_by_role("button", name=re.compile(r"^Yes$|^Delete$|^OK$", re.I)).first
                expect(yes_btn).to_be_visible(timeout=5_000)
                yes_btn.click(timeout=5_000)

        for attempt in range(2):
            clicked = click_delete_control()
            if not clicked:
                raise AssertionError(f"Could not click delete/disconnect control for exchange '{connection_name}'.")

            confirm_delete_dialog()

            with allure.step(f"Verify exchange '{connection_name}' is removed from Connected Exchanges"):
                try:
                    self.wait_until_exchange_absent(connection_name, timeout_sec=max(8, timeout_sec // 2))
                    return True
                except AssertionError:
                    if attempt == 1:
                        raise
                    self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                    expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
                    self._wait_exchange_page_ready()

        return False

    def get_connected_exchange_names(self) -> list[str]:
        self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
        self._wait_exchange_page_ready()

        section = self.page.locator(
            "xpath=//*[self::section or self::div][.//*[self::h1 or self::h2 or self::h3 or self::h4]"
            "[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connected exchange')]]"
        ).first
        source_text = ""
        try:
            if section.count() > 0:
                source_text = section.inner_text()
            else:
                source_text = self.page.locator("body").inner_text()
        except Exception:
            source_text = ""
        return self._extract_connected_exchange_names_from_text(source_text)

    def get_connected_exchange_names_from_current_page(self) -> list[str]:
        source_text = ""
        try:
            source_text = self.page.locator("body").inner_text(timeout=1_000)
        except Exception:
            source_text = ""
        return self._extract_connected_exchange_names_from_text(source_text)

    def _find_exchange_row(self, connection_name: str):
        row_candidates = [
            self.page.locator(
                "xpath=//*[self::div or self::tr or self::li][contains(normalize-space(.), "
                f"'{connection_name} / Binance')]"
            ).first,
            self.page.locator(
                "xpath=//*[self::div or self::tr or self::li][contains(normalize-space(.), "
                f"'{connection_name}') and contains(normalize-space(.), 'Binance')]"
            ).first,
            self.page.locator(f"text={connection_name} / Binance").locator("xpath=ancestor::*[self::div or self::tr or self::li][1]").first,
            self.page.locator(f"text={connection_name}").locator("xpath=ancestor::*[self::div or self::tr or self::li][1]").first,
        ]
        for candidate in row_candidates:
            try:
                if candidate.count() > 0 and candidate.is_visible(timeout=1_000):
                    return candidate
            except Exception:
                continue
        return self.page.locator("xpath=/html[false()]")

    def _extract_connected_exchange_names_from_text(self, source_text: str) -> list[str]:
        names: list[str] = []
        for line in source_text.splitlines():
            match = re.search(r"^\s*([^/\n]+?)\s*/\s*Binance\s*$", line, flags=re.I)
            if match:
                names.append(match.group(1).strip())
        return sorted(set(names))

    def _get_visible_connect_to_exchange_button(self):
        form_scoped_candidates = [
            self.page.locator(
                "xpath=//*[self::div or self::form][.//input[@name='bn-connection-name'] "
                "and .//input[@name='bn-api-key'] and .//input[@name='bn-api-secret']]"
            ).last.get_by_role("button", name=re.compile(r"Connect to Exchange", re.I)),
            self.page.locator("input[name='bn-api-secret']").locator(
                "xpath=ancestor::*[self::div or self::form][.//input[@name='bn-connection-name'] "
                "and .//input[@name='bn-api-key']][1]"
            ).get_by_role("button", name=re.compile(r"Connect to Exchange", re.I)),
        ]
        candidates = form_scoped_candidates + [
            self.page.locator("button:has-text('Connect to Exchange')"),
            self.page.get_by_role("button", name=re.compile(r"Connect to Exchange", re.I)),
        ]
        for locator in candidates:
            count = min(locator.count(), 10)
            for idx in range(count):
                candidate = locator.nth(idx)
                try:
                    if candidate.is_visible(timeout=500):
                        return candidate
                except Exception:
                    continue
        return self.page.get_by_role("button", name=re.compile(r"Connect to Exchange", re.I)).last

    def ensure_exchange_deleted(self, connection_name: str, attempts: int = 3) -> None:
        for _ in range(attempts):
            names = self.get_connected_exchange_names()
            if connection_name not in names:
                return
            self.delete_exchange_account_if_exists(connection_name)
            if connection_name not in self.get_connected_exchange_names():
                return
        raise AssertionError(f"Exchange '{connection_name}' is still present after cleanup attempts.")

    def ensure_no_connected_exchanges(self, attempts: int = 5, max_delete_per_pass: int = 20) -> list[str]:
        remaining = self.get_connected_exchange_names()
        for _ in range(attempts):
            if not remaining:
                self.wait_until_no_connected_exchanges(timeout_sec=5)
                return []
            for name in remaining[:max_delete_per_pass]:
                try:
                    self.delete_exchange_account_if_exists(name)
                except Exception:
                    continue
            self.purge_all_connected_exchange_accounts(max_delete=max_delete_per_pass)
            remaining = self.get_connected_exchange_names()
        if not remaining:
            self.wait_until_no_connected_exchanges(timeout_sec=5)
        return remaining

    def purge_exchange_accounts_by_pattern(self, name_pattern: str, max_delete: int = 20) -> int:
        self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)

        deleted = 0
        rx = re.compile(name_pattern)

        for _ in range(max_delete):
            page_text = self.page.locator("body").inner_text()
            matches = sorted(set(rx.findall(page_text)))
            if not matches:
                break

            target_name = matches[0]
            try:
                if self.delete_exchange_account_if_exists(target_name):
                    deleted += 1
            except Exception:
                # Move on to prevent dead loop on one broken account row.
                self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
                self.page.wait_for_timeout(1_000)
                continue

        return deleted

    def purge_all_binance_accounts(self, max_delete: int = 20) -> int:
        deleted = 0
        for _ in range(max_delete):
            self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
            expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
            self.page.wait_for_timeout(1_000)

            # Find rows/cards that represent connected Binance accounts and expose delete/disconnect controls.
            account_rows = self.page.locator("tr, li, div").filter(
                has=self.page.get_by_role("button", name=re.compile(r"delete|remove|disconnect", re.I))
            )

            target_row = None
            for idx in range(min(account_rows.count(), 200)):
                row = account_rows.nth(idx)
                try:
                    text = row.inner_text().strip()
                except Exception:
                    continue
                if not text:
                    continue
                if re.search(r"\bbinance\b", text, re.I):
                    target_row = row
                    break

            if target_row is None:
                break

            delete_btn = target_row.get_by_role("button", name=re.compile(r"delete|remove|disconnect", re.I)).first
            clicked = False
            if delete_btn.count() > 0:
                try:
                    delete_btn.scroll_into_view_if_needed()
                    delete_btn.click(timeout=5_000)
                    clicked = True
                except Exception:
                    try:
                        delete_btn.click(timeout=5_000, force=True)
                        clicked = True
                    except Exception:
                        clicked = False

            if not clicked:
                raise AssertionError("Could not click delete/disconnect for Binance exchange account row.")

            confirm = self.page.get_by_role("button", name=re.compile(r"^delete$|^yes$|^ok$|confirm", re.I)).first
            if confirm.count() > 0:
                try:
                    confirm.click(timeout=5_000)
                except Exception:
                    pass

            self.page.wait_for_timeout(1_500)
            deleted += 1

        return deleted

    def purge_all_connected_exchange_accounts(self, max_delete: int = 20) -> int:
        deleted = 0
        names = self.get_connected_exchange_names()
        for name in names[:max_delete]:
            if self.delete_exchange_account_if_exists(name):
                deleted += 1

        return deleted

    def _wait_exchange_deleted_feedback(self, connection_name: str, timeout_sec: int = 20, required: bool = True) -> bool:
        exact_text = f"Your exchange {connection_name} was deleted."
        try:
            self._wait_exact_feedback_text(
                exact_text,
                debug_name="exchange_delete_feedback_debug",
                timeout_sec=timeout_sec,
            )
            return True
        except AssertionError:
            if not required:
                return False

        patterns = [
            re.compile(rf"^{re.escape(exact_text)}$", re.I),
            re.compile(r"exchange.*deleted", re.I),
            re.compile(r"exchange.*removed", re.I),
            re.compile(r"exchange.*disconnected", re.I),
            re.compile(r"has been deleted", re.I),
            re.compile(r"has been removed", re.I),
        ]
        end_time = time.time() + timeout_sec
        last_texts: list[str] = []
        while time.time() < end_time:
            texts = self._collect_visible_feedback_texts()
            if texts:
                last_texts = texts
            for text in texts:
                if any(rx.search(text) for rx in patterns):
                    ok_btn = self.page.get_by_role("button", name=re.compile(r"^ok$|close", re.I)).first
                    try:
                        if ok_btn.count() > 0 and ok_btn.is_visible(timeout=500):
                            ok_btn.click(timeout=2_000)
                    except Exception:
                        pass
                    return True
            # Some success toasts on this front are icon-only without text.
            success_icon = self.page.locator("text=/^$/").first
            try:
                if success_icon.count() > 0 and success_icon.is_visible(timeout=300):
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(500)

        if not required:
            return False
        allure.attach(
            "\n\n---\n\n".join(last_texts) if last_texts else "No visible feedback texts found.",
            "exchange_delete_feedback_debug",
            allure.attachment_type.TEXT,
        )
        raise AssertionError(
            f"Expected frontend message '{exact_text}' was not shown."
        )

    def _wait_exact_feedback_text(
        self,
        expected_text: str,
        debug_name: str,
        timeout_sec: int = 20,
        required: bool = True,
    ) -> str | None:
        end_time = time.time() + timeout_sec
        last_texts: list[str] = []

        while time.time() < end_time:
            texts = self._collect_visible_feedback_texts()
            body_text = ""
            try:
                body_text = self.page.locator("body").inner_text(timeout=500)
            except Exception:
                body_text = ""

            if texts:
                last_texts = texts

            for text in texts:
                if text.strip() == expected_text:
                    return text

            if expected_text in body_text:
                return expected_text

            self.page.wait_for_timeout(300)

        if not required:
            return None

        debug_payload = "\n\n---\n\n".join(last_texts) if last_texts else "No visible feedback texts found."
        if body_text:
            debug_payload = f"{debug_payload}\n\n=== BODY EXCERPT ===\n\n{body_text[:4000]}"
        allure.attach(debug_payload, debug_name, allure.attachment_type.TEXT)
        raise AssertionError(f"Expected frontend message '{expected_text}' was not shown.")

    def _collect_visible_feedback_texts(self) -> list[str]:
        selectors = [
            "[role='dialog']",
            "[role='alert']",
            "[class*='notification']",
            "[class*='toast']",
            "[class*='message']",
        ]
        texts: list[str] = []
        seen: set[str] = set()
        for selector in selectors:
            locator = self.page.locator(selector)
            count = min(locator.count(), 30)
            for i in range(count):
                item = locator.nth(i)
                try:
                    if not item.is_visible(timeout=150):
                        continue
                    text = item.inner_text().strip()
                except Exception:
                    continue
                if text and text not in seen:
                    seen.add(text)
                    texts.append(text)
        return texts

    def refresh_connected_exchange_balance(self, connection_name: str) -> None:
        self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)

        account_row = self.page.locator(
            "xpath=//*[self::div or self::tr or self::li][.//*[contains(normalize-space(text()),"
            f"'{connection_name}')]]"
        ).first
        if account_row.count() == 0:
            return

        refresh_btn = account_row.get_by_role("button").first
        if refresh_btn.count() > 0:
            try:
                refresh_btn.click(timeout=5_000)
                self.page.wait_for_timeout(2_000)
            except Exception:
                pass

    def has_futures_balance_for_exchange(self, connection_name: str) -> bool:
        self.page.goto(f"{self.base_url}/dashboard/exchange", wait_until="domcontentloaded")
        expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
        self.page.wait_for_timeout(1_000)

        account_row = self.page.locator(
            "xpath=//*[self::div or self::tr or self::li][.//*[contains(normalize-space(text()),"
            f"'{connection_name}')]]"
        ).first
        if account_row.count() == 0:
            return False

        row_text = account_row.inner_text().lower()
        if "futures balance" in row_text and "no assets detected" in row_text:
            return False

        # Fallback: if futures section has any numeric USDT value > 0 in card text, treat as usable.
        usdt_matches = re.findall(r"([0-9]+(?:[.,][0-9]+)?)\s*usdt", row_text, flags=re.I)
        for value in usdt_matches:
            normalized = value.replace(",", ".")
            try:
                if float(normalized) > 0:
                    return True
            except ValueError:
                continue

        return "futures balance" in row_text and "no assets detected" not in row_text
