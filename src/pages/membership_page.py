import re
import time
from typing import Any

import allure
from playwright.sync_api import Locator, Page, expect

from src.pages.marketplace_page import MarketplacePage


class MembershipPage(MarketplacePage):
    PATH = "/dashboard/membership"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def open(self) -> None:
        with allure.step("Open the Membership page"):
            self.page.goto(f"{self.base_url}{self.PATH}", wait_until="domcontentloaded")
        self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        with allure.step("Wait for Membership content to load"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/membership"), timeout=30_000)
            expect(self.page.get_by_text(re.compile(r"Pre-paid Plans", re.I)).first).to_be_visible(timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(r"x3", re.I), timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(r"x5", re.I), timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(r"UNLIMITED", re.I), timeout=30_000)
            self.page.wait_for_function(
                "() => !(document.body && document.body.innerText.includes('Loading'))",
                timeout=30_000,
            )
            expect(self.page.locator("body")).to_contain_text(re.compile(r"Your memberships history:", re.I), timeout=30_000)

    def measure_warm_load(self) -> float:
        with allure.step("Measure warm load time for Membership page"):
            self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_function(
                """
                () => {
                    const entries = performance.getEntriesByType('navigation');
                    const nav = entries[entries.length - 1];
                    return Boolean(nav && nav.domContentLoadedEventEnd > 0);
                }
                """,
                timeout=10_000,
            )
            duration_ms = self.page.evaluate(
                """
                () => {
                    const entries = performance.getEntriesByType('navigation');
                    const nav = entries[entries.length - 1];
                    if (nav && nav.domContentLoadedEventEnd > 0) return nav.domContentLoadedEventEnd;
                    return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart;
                }
                """
            )
            self.wait_until_loaded()
            duration_sec = float(duration_ms) / 1000
            allure.attach(f"{duration_sec:.2f} sec", "membership_warm_load_duration", allure.attachment_type.TEXT)
            return duration_sec

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Pre-paid Plans", re.I)).first

    def start_now_buttons(self) -> Locator:
        return self.page.locator("text=Start now")

    def open_plan_modal_by_start_index(self, index: int):
        target = self.start_now_buttons().nth(index)
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_timeout(800)

    def modal(self) -> Locator:
        return self.page.get_by_role("dialog").first

    def modal_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def close_modal(self) -> None:
        visible_dialog = self.page.locator('[role="dialog"]:visible').last
        close_candidates = [
            visible_dialog.locator(".el-dialog__headerbtn:visible").first,
            visible_dialog.get_by_role("button", name=re.compile(r"close", re.I)).first,
            visible_dialog.locator('button[aria-label*="close" i]:visible').first,
        ]
        for candidate in close_candidates:
            try:
                if candidate.count() > 0:
                    candidate.click(timeout=2_000, force=True)
                    self.page.wait_for_function(
                        "() => !document.body.innerText.includes('You have selected')",
                        timeout=5_000,
                    )
                    return
            except Exception:
                continue
        self.page.keyboard.press("Escape")
        self.page.wait_for_function(
            "() => !document.body.innerText.includes('You have selected')",
            timeout=5_000,
        )

    def open_coinpayments_popup(self):
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("button", name=re.compile(r"^BUY$", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        popup.wait_for_timeout(2_500)
        return popup

    def history_rows(self) -> list[list[str]]:
        tables = self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('table')).map((table) =>
                Array.from(table.querySelectorAll('tr')).map((row) =>
                    Array.from(row.querySelectorAll('th, td'))
                        .map((cell) => (cell.innerText || '').replace(/\\s+/g, ' ').trim())
                        .filter(Boolean)
                ).filter((row) => row.length > 0)
            )
            """
        )
        header_set = {"Name", "Payment", "Status", "Start Date", "Expiration date"}
        for table in tables:
            if table and all(len(row) >= 5 for row in table):
                flat = [cell for row in table for cell in row]
                if not header_set.issubset(set(flat)):
                    return [row[:5] for row in table if len(row) >= 5]
        return []

    def history_headers(self) -> list[str]:
        tables = self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('table')).map((table) =>
                Array.from(table.querySelectorAll('tr')).map((row) =>
                    Array.from(row.querySelectorAll('th, td'))
                        .map((cell) => (cell.innerText || '').replace(/\\s+/g, ' ').trim())
                        .filter(Boolean)
                ).filter((row) => row.length > 0)
            )
            """
        )
        header_set = {"Name", "Payment", "Status", "Start Date", "Expiration date"}
        for table in tables:
            flat = [cell for row in table for cell in row]
            if header_set.issubset(set(flat)):
                return table[0]
        return []


class CoinPaymentsCheckoutPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_until_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"coinpayments\.net/index\.php"), timeout=30_000)
        expect(self.page.locator("body")).to_contain_text(re.compile(r"Securely processed by CoinPayments\.net", re.I), timeout=30_000)

    def measure_load(self) -> float:
        self.page.wait_for_function(
            """
            () => {
                const entries = performance.getEntriesByType('navigation');
                const nav = entries[entries.length - 1];
                return Boolean(nav && nav.domContentLoadedEventEnd > 0);
            }
            """,
            timeout=10_000,
        )
        duration_ms = self.page.evaluate(
            """
            () => {
                const entries = performance.getEntriesByType('navigation');
                const nav = entries[entries.length - 1];
                if (nav && nav.domContentLoadedEventEnd > 0) return nav.domContentLoadedEventEnd;
                return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart;
            }
            """
        )
        duration_sec = float(duration_ms) / 1000
        allure.attach(f"{duration_sec:.2f} sec", "coinpayments_load_duration", allure.attachment_type.TEXT)
        return duration_sec

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def select_coin(self, label: str) -> None:
        target = self.page.locator(f"text={label}").first
        target.click()
        self.page.wait_for_timeout(600)

    def click_complete_checkout(self) -> None:
        self.page.locator("text=Complete Checkout").click()
        self.page.wait_for_timeout(800)
