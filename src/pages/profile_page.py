import re
import time
from urllib.parse import parse_qs, urlparse

import allure
from playwright.sync_api import Locator, Page, expect

from src.utils.allure_helpers import attach_expected_actual, attach_input_payload


class ProfilePage:
    PROFILE_PATH = "/dashboard/profile"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.last_load_duration_seconds: float | None = None
        self.last_load_metric_name: str | None = None
        self._api_auth_header: str | None = None

    def open(self) -> None:
        started_at = time.monotonic()
        with allure.step("Open the Profile page"):
            self.page.goto(f"{self.base_url}{self.PROFILE_PATH}", wait_until="domcontentloaded")
        self._wait_ready()
        browser_navigation_metric = self.page.evaluate(
            """
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                if (!navigation) return null;
                const metrics = [
                    ['domContentLoaded', navigation.domContentLoadedEventEnd],
                    ['responseEnd', navigation.responseEnd],
                    ['loadEventEnd', navigation.loadEventEnd],
                    ['domComplete', navigation.domComplete],
                ];
                for (const [name, value] of metrics) {
                    if (Number.isFinite(value) && value > 0) {
                        return { name, seconds: value / 1000 };
                    }
                }
                return null;
            }
            """
        )
        if browser_navigation_metric:
            self.last_load_metric_name = str(browser_navigation_metric["name"])
            self.last_load_duration_seconds = float(browser_navigation_metric["seconds"])
        else:
            self.last_load_metric_name = "ui_ready"
            self.last_load_duration_seconds = time.monotonic() - started_at
        allure.attach(
            f"{self.last_load_metric_name}={self.last_load_duration_seconds:.3f}",
            "profile_page_load_seconds",
            allure.attachment_type.TEXT,
        )
        allure.attach(
            f"{time.monotonic() - started_at:.3f}",
            "profile_page_ui_ready_seconds",
            allure.attachment_type.TEXT,
        )

    def _wait_ready(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/dashboard/profile"), timeout=30_000)
        expect(self.page.get_by_role("heading", name=re.compile(r"^My Profile$", re.I))).to_be_visible(timeout=30_000)
        expect(self.page.get_by_role("heading", name=re.compile(r"^Notification$", re.I))).to_be_visible(timeout=30_000)

    def heading(self, text: str, level: int | None = None) -> Locator:
        if level is None:
            return self.page.get_by_role("heading", name=re.compile(rf"^{re.escape(text)}$", re.I)).first
        return self.page.get_by_role("heading", name=re.compile(rf"^{re.escape(text)}$", re.I), level=level).first

    def assert_load_time_not_more_than(self, max_seconds: float) -> None:
        assert self.last_load_duration_seconds is not None, "Profile page was not opened through ProfilePage.open()."
        attach_expected_actual(
            f"load time ({self.last_load_metric_name}) <= {max_seconds:.3f}s",
            f"actual load time ({self.last_load_metric_name}) = {self.last_load_duration_seconds:.3f}s",
        )
        assert self.last_load_duration_seconds <= max_seconds, self.last_load_duration_seconds

    def measure_warm_load(self) -> None:
        with allure.step("Measure the warm reload time of the Profile page"):
            self.page.goto(f"{self.base_url}{self.PROFILE_PATH}", wait_until="domcontentloaded")
            self._wait_ready()
            navigation = self.page.evaluate(
                """
                () => {
                    const nav = performance.getEntriesByType('navigation')[0];
                    if (!nav) return null;
                    return {
                        domContentLoaded: nav.domContentLoadedEventEnd / 1000,
                        responseEnd: nav.responseEnd / 1000,
                        loadEventEnd: nav.loadEventEnd / 1000,
                        domComplete: nav.domComplete / 1000,
                    };
                }
                """
            )
            metric_name = "domContentLoaded"
            metric_value = float(navigation.get(metric_name) or 0) if navigation else 0.0
            if metric_value <= 0 and navigation:
                for fallback_name in ("domComplete", "loadEventEnd", "responseEnd"):
                    fallback_value = float(navigation.get(fallback_name) or 0)
                    if fallback_value > 0:
                        metric_name = fallback_name
                        metric_value = fallback_value
                        break
            self.last_load_metric_name = f"warm_{metric_name}"
            self.last_load_duration_seconds = metric_value
            allure.attach(
                str(navigation),
                "profile_page_warm_navigation_metrics",
                allure.attachment_type.TEXT,
            )

    def telegram_bot_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"(Activate|Deactivate) Telegram bot", re.I)).first

    def telegram_bot_button_text(self) -> str:
        return self.telegram_bot_button().inner_text().strip()

    def telegram_connected(self) -> bool:
        return bool(self.telegram_api_state()["telegram_connection"])

    def telegram_api_state(self) -> dict:
        headers = self._telegram_api_headers()
        response = self.page.context.request.get(
            "https://api.gt-protocol.io/api/v1/user/me/telegram",
            headers=headers,
        )
        status = response.status() if callable(getattr(response, "status", None)) else response.status
        assert status == 200, response.text()
        return response.json()

    def _telegram_api_headers(self) -> dict[str, str]:
        if not self._api_auth_header:
            self._api_auth_header = self._capture_api_auth_header()
        return {
            "authorization": self._api_auth_header,
            "x-user-agent": "GTAPP",
            "locale": "en",
            "referer": "https://app.gt-protocol.io/",
            "content-type": "application/json;charset=UTF-8",
        }

    def _capture_api_auth_header(self) -> str:
        initial_state = self.notification_toggle_checked()
        captured_auth: str | None = None

        def on_request(request) -> None:
            nonlocal captured_auth
            if "/api/v1/user/me/telegram" in request.url:
                captured_auth = request.headers.get("authorization")

        self.page.on("request", on_request)
        try:
            self.click_notification_toggle()
        finally:
            self.page.remove_listener("request", on_request)

        if self.notification_toggle_checked() != initial_state:
            self.click_notification_toggle()

        if not captured_auth:
            raise AssertionError("Could not capture Telegram API authorization header from the authenticated session.")
        return captured_auth

    def notification_toggle(self) -> Locator:
        return self.page.locator("input[type='checkbox']").first

    def notification_switch(self) -> Locator:
        return self.page.get_by_role("switch").first

    def notification_toggle_checked(self) -> bool:
        return self.notification_toggle().is_checked()

    def click_notification_toggle(self) -> None:
        with allure.step("Toggle 'Send All notifications'"):
            initial_state = self.notification_toggle_checked()
            click_attempts = [
                lambda: self.notification_switch().click(force=True),
                lambda: self.notification_toggle().click(force=True),
                lambda: self.page.evaluate(
                    "() => document.querySelector('input[type=\"checkbox\"]')?.click()"
                ),
            ]
            for attempt in click_attempts:
                attempt()
                try:
                    self.page.wait_for_function(
                        "(expected) => !!document.querySelector('input[type=\"checkbox\"]') && "
                        "document.querySelector('input[type=\"checkbox\"]').checked !== expected",
                        arg=initial_state,
                        timeout=2_000,
                    )
                    self.page.wait_for_timeout(500)
                    return
                except Exception:
                    continue
            raise AssertionError("Notification toggle did not change state after multiple click strategies.")

    def notification_exception_list_present(self) -> bool:
        body_text = self.page.locator("body").inner_text(timeout=10_000)
        return all(item in body_text for item in self.notification_exception_items())

    def assert_notification_toggle_visible(self) -> None:
        with allure.step("Verify the notification toggle is visible"):
            expect(self.page.get_by_text(re.compile(r"^Send All notifications:", re.I))).to_be_visible()
            expect(self.notification_switch()).to_be_visible()

    def notification_exception_items(self) -> list[str]:
        return [
            "Strategy starts Deal",
            "Strategy activating trailing",
            "Take profit order was executed",
            "Deal completed",
            "Total strategy profit",
        ]

    def assert_notification_exception_list_visible(self) -> None:
        with allure.step("Verify the notification exception list is visible"):
            body_text = self.page.locator("body").inner_text(timeout=10_000)
            for item in self.notification_exception_items():
                assert item in body_text, f"Expected exception list item missing from visible text: {item}"

    def assert_notification_exception_list_hidden(self) -> None:
        with allure.step("Verify the notification exception list is hidden"):
            body_text = self.page.locator("body").inner_text(timeout=10_000)
            for item in self.notification_exception_items():
                assert item not in body_text, f"Unexpected exception list item still visible: {item}"

    def open_telegram_bot_activation(self) -> Page:
        with allure.step("Open Telegram bot activation page"):
            with self.page.context.expect_page(timeout=10_000) as popup_info:
                self.telegram_bot_button().click()
            popup = popup_info.value
            popup.wait_for_load_state("domcontentloaded", timeout=10_000)
            return popup

    def deactivate_telegram_bot(self) -> None:
        with allure.step("Deactivate the connected Telegram bot"):
            self.telegram_bot_button().click()
            self.page.wait_for_timeout(1500)

    def assert_telegram_activation_popup(self, popup: Page) -> None:
        with allure.step("Verify the Telegram activation page opened in a new tab"):
            parsed = urlparse(popup.url)
            query = parse_qs(parsed.query)
            allure.attach(popup.url, "telegram_activation_url", allure.attachment_type.TEXT)
            assert parsed.netloc in {"telegram.me", "t.me"}, popup.url
            assert re.search(r"/Notifications_Jet_Bot/?$", parsed.path), popup.url
            assert "start" in query and query["start"][0], popup.url

    def binance_link_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Link Binance Account$", re.I)).first

    def assert_binance_info_text_visible(self) -> None:
        with allure.step("Verify the Binance account info text is visible"):
            body_text = self.page.locator("body").inner_text(timeout=10_000)
            assert "This account is connected to a Binance account via" in body_text, body_text
            expect(
                self.page.get_by_text(
                    re.compile(
                        r"This account is connected to a Binance account via.+You can connect another Binance account using the form below",
                        re.I,
                    )
                ).first
            ).to_be_visible()

    def assert_binance_subtitle_visible(self) -> None:
        with allure.step("Verify the Binance account subtitle is visible"):
            expect(
                self.page.get_by_text(
                    re.compile(r"Link your Binance account, and open a copy with one click", re.I)
                ).first
            ).to_be_visible()

    def open_binance_oauth(self) -> None:
        with allure.step("Open Binance OAuth flow"):
            self.binance_link_button().click()
            self.page.wait_for_load_state("domcontentloaded", timeout=15_000)

    def assert_binance_oauth_opened(self) -> None:
        with allure.step("Verify Binance OAuth opened in the same tab"):
            expect(self.page).to_have_url(re.compile(r"^https://accounts\.binance\.com", re.I), timeout=20_000)

    def delete_account_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Delete account$", re.I)).first

    def open_delete_account_modal(self) -> None:
        with allure.step("Open the delete account modal"):
            self.delete_account_button().click()
            expect(self.delete_account_modal()).to_be_visible(timeout=10_000)

    def delete_account_modal(self) -> Locator:
        return self.page.locator("[role='dialog']").filter(
            has=self.page.get_by_role("heading", name=re.compile(r"Deleting Your Account", re.I))
        ).first

    def modal_close_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Close$", re.I)).first

    def keep_my_account_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Keep my account$", re.I)).first

    def delete_account_confirm_button(self) -> Locator:
        return self.delete_account_modal().get_by_role("button", name=re.compile(r"^Delete account$", re.I)).last

    def delete_modal_checkbox(self, label: str) -> Locator:
        return self.delete_account_modal().get_by_role("checkbox", name=re.compile(re.escape(label), re.I)).first

    def delete_modal_progress_text(self) -> Locator:
        return self.delete_account_modal().locator("text=/\\d+ of 4 steps completed/i").first

    def tick_all_delete_modal_checkboxes(self) -> None:
        labels = [
            "You have stopped all active strategies (personal and copied).",
            "You have stopped and disabled all Portfolios.",
            "You have disconnected all exchange API connections.",
            "You have disabled notifications from the Telegram bot",
        ]
        with allure.step("Tick all delete-account confirmation checkboxes"):
            for label in labels:
                checkbox = self.delete_modal_checkbox(label)
                if not checkbox.is_checked():
                    checkbox.click(force=True)
            expect(self.delete_modal_progress_text()).to_have_text(re.compile(r"4 of 4 steps completed", re.I))

    def close_delete_modal_with_keep_account(self) -> None:
        with allure.step("Close the delete account modal via 'Keep my account'"):
            self.keep_my_account_button().click()
            expect(self.delete_account_modal()).not_to_be_visible(timeout=10_000)

    def close_delete_modal_with_close_button(self) -> None:
        with allure.step("Close the delete account modal via close button"):
            self.modal_close_button().click()
            expect(self.delete_account_modal()).not_to_be_visible(timeout=10_000)

    def uid_value(self) -> str:
        candidates = [
            self.page.locator("xpath=//*[normalize-space(text())='UID']/following-sibling::*[1]").first,
            self.page.get_by_text(re.compile(r"UID:\s*\d+", re.I)).first,
        ]
        for candidate in candidates:
            try:
                text = candidate.inner_text(timeout=2_000).strip()
            except Exception:
                continue
            match = re.search(r"\d+", text)
            if match:
                return match.group(0)
        raise AssertionError("UID value was not found on the Profile page.")

    def email_value(self) -> str:
        candidates = [
            self.page.locator("xpath=//*[normalize-space(text())='Email']/following-sibling::*[1]").first,
            self.page.get_by_text(re.compile(r"@", re.I)).first,
        ]
        for candidate in candidates:
            try:
                text = candidate.inner_text(timeout=2_000).strip()
            except Exception:
                continue
            if "@" in text:
                return text
        raise AssertionError("Email value was not found on the Profile page.")

    def password_input(self, placeholder: str) -> Locator:
        return self.page.locator(f"input[placeholder='{placeholder}']").first

    def password_visibility_toggle(self, placeholder: str) -> Locator:
        return self.password_input(placeholder).locator(
            "xpath=ancestor::*[contains(@class, 'el-form-item__content')][1]//*[contains(@class, 'show-pwd')]"
        ).first

    def fill_password_form(self, current_password: str = "", new_password: str = "", confirm_password: str = "") -> None:
        with allure.step("Fill the password update form"):
            attach_input_payload(
                {
                    "current_password": "***" if current_password else "",
                    "new_password": "***" if new_password else "",
                    "confirm_password": "***" if confirm_password else "",
                }
            )
            self.password_input("Current Password").fill(current_password)
            self.password_input("New Password").fill(new_password)
            self.password_input("Confirm Password").fill(confirm_password)

    def click_save_password(self) -> None:
        with allure.step("Submit the password update form"):
            self.page.get_by_role("button", name=re.compile(r"^Save Password$", re.I)).click()

    def required_password_errors(self) -> Locator:
        return self.page.locator("text=/Field is required\\./i")

    def password_form_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def assert_password_validation_message(self, pattern: str) -> None:
        with allure.step(f"Verify password validation message matches /{pattern}/"):
            text = self.password_form_text()
            match = re.search(pattern, text, re.I)
            assert match, text
            allure.attach(match.group(0), "password_validation_match", allure.attachment_type.TEXT)

    def changelog_dates(self) -> list[str]:
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('*'))
                .map((el) => (el.textContent || '').trim())
                .filter((value) => /^\\d{2}\\.\\d{2}\\.\\d{4}$/.test(value))
            """
        )

    def changelog_scroll_metrics(self) -> dict[str, int | bool]:
        return self.page.evaluate(
            """
            () => {
                const heading = Array.from(document.querySelectorAll('*')).find(
                    (el) => (el.textContent || '').trim() === 'Changelog'
                );
                if (!heading) return { found: false, scrollHeight: 0, clientHeight: 0 };

                let container = heading.parentElement;
                while (container) {
                    if (container.scrollHeight > container.clientHeight + 10) {
                        return {
                            found: true,
                            scrollHeight: container.scrollHeight,
                            clientHeight: container.clientHeight,
                        };
                    }
                    container = container.parentElement;
                }
                return { found: true, scrollHeight: 0, clientHeight: 0 };
            }
            """
        )
