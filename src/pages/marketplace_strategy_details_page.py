import re
import time
from typing import Any

import allure
from playwright.sync_api import Locator, expect

from src.pages.marketplace_page import MarketplacePage


class MarketplaceStrategyDetailsPage(MarketplacePage):
    DETAILS_URL_RE = re.compile(r"/dashboard/bots-marketplace/statistics/(\d+)/")

    def open_first_strategy_details(self) -> None:
        with allure.step("Open the first Marketplace strategy details page"):
            super().open()
            first_card = self.first_strategy_card()
            self.click_strategy_button(first_card, "Details")
            self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        with allure.step("Wait for Marketplace strategy details content to become visible"):
            expect(self.page).to_have_url(self.DETAILS_URL_RE, timeout=30_000)
            expect(self.detail_heading()).to_be_visible(timeout=30_000)
            expect(self.list_of_strategies_button()).to_be_visible(timeout=30_000)
            expect(self.copy_button()).to_be_visible(timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(r"Deals History", re.I), timeout=30_000)

    def measure_warm_load(self) -> float:
        with allure.step("Measure warm load time for the strategy details page"):
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
                    if (nav && nav.domContentLoadedEventEnd > 0) {
                        return nav.domContentLoadedEventEnd;
                    }
                    return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart;
                }
                """
            )
            self.wait_until_loaded()
            duration_sec = float(duration_ms) / 1000
            allure.attach(f"{duration_sec:.2f} sec", "strategy_details_warm_load_duration", allure.attachment_type.TEXT)
            return duration_sec

    def detail_heading(self) -> Locator:
        return self.page.get_by_role("heading").first

    def list_of_strategies_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^List of Strategies$", re.I)).first

    def copy_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^COPY$", re.I)).first

    def footer_copyright(self) -> Locator:
        return self.page.locator("text=/©\\s*2026\\s*GT App/i").first

    def _page_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def summary_text(self) -> str:
        text = self._page_text()
        if "Deals History" in text:
            return text.split("Deals History", 1)[0]
        return text

    def heading_text(self) -> str:
        return self.detail_heading().inner_text(timeout=10_000).strip()

    def trader_avatar(self) -> Locator:
        return self.page.locator("img").first

    def trader_name(self) -> str:
        text = self.summary_text()
        match = re.search(r"Made by\s+([^\n]+)", text, re.I)
        if match:
            return match.group(1).strip()
        heading_match = re.search(r"strategy by Top Trader\s+(.+)$", self.heading_text(), re.I)
        return heading_match.group(1).strip() if heading_match else ""

    def apy_value(self) -> str:
        return self._summary_value(r"APY\s+([+-]?\d+(?:\.\d+)?%)")

    def lifetime_value(self) -> str:
        return self._summary_value(r"Lifetime\s+(\d+\s*D)")

    def risk_value(self) -> str:
        return self._summary_value(r"Risk\s+(High|Medium|Low)")

    def min_balance_value(self) -> str:
        return self._summary_value(r"Min\.\s*Balance\s+([+-]?\d+(?:\.\d+)?\s*USDT)")

    def total_profit_value(self) -> str:
        return self._summary_value(r"Total profit:\s*([+-]?\d+(?:\.\d+)?\s*USDT)")

    def _summary_value(self, pattern: str) -> str:
        for source in (self.summary_text(), self._page_text()):
            match = re.search(pattern, source, re.I)
            if match:
                return match.group(1).strip()
        return ""

    def about_strategy_toggle(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^About Strategy$", re.I)).first

    def about_strategy_item(self) -> Locator:
        return self.about_strategy_toggle().locator("xpath=ancestor::*[contains(@class, 'el-collapse-item')][1]")

    def about_strategy_content(self) -> Locator:
        return self.about_strategy_item().locator(".el-collapse-item__content").first

    def is_about_strategy_expanded(self) -> bool:
        item = self.about_strategy_item()
        class_name = item.get_attribute("class") or ""
        return "is-active" in class_name

    def about_strategy_text(self) -> str:
        try:
            return self.about_strategy_content().inner_text(timeout=3_000).strip()
        except Exception:
            return ""

    def click_about_strategy(self) -> None:
        self._assert_target_actionable(self.about_strategy_toggle())
        self._click_target(self.about_strategy_toggle())
        self.page.wait_for_timeout(500)

    def top_trader_profit_chart_toggle(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Top Trader Profit Chart$", re.I)).first

    def top_trader_profit_chart_canvases(self) -> Locator:
        return self.page.locator(".chart-wrapper canvas")

    def top_trader_profit_chart_has_non_blank_canvas(self) -> bool:
        return bool(
            self.page.evaluate(
                """
                () => {
                    const canvases = Array.from(document.querySelectorAll('.chart-wrapper canvas'));
                    const hasVisibleCanvas = canvases.some((canvas) => {
                        if (!canvas.width || !canvas.height) return false;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return false;
                        const width = Math.max(1, Math.min(canvas.width, 64));
                        const height = Math.max(1, Math.min(canvas.height, 64));
                        const image = ctx.getImageData(0, 0, width, height).data;
                        let colored = 0;
                        for (let i = 0; i < image.length; i += 4) {
                            const alpha = image[i + 3];
                            const r = image[i];
                            const g = image[i + 1];
                            const b = image[i + 2];
                            if (alpha > 0 && !(r > 245 && g > 245 && b > 245)) {
                                colored += 1;
                            }
                        }
                        return colored > 100;
                    });
                    return hasVisibleCanvas;
                }
                """
            )
        )

    def bot_id(self) -> str:
        match = self.DETAILS_URL_RE.search(self.page.url)
        if not match:
            raise AssertionError(f"Could not parse bot id from strategy details URL: {self.page.url}")
        return match.group(1)

    def tradingview_frame(self):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            frame = self.page.frame(url=re.compile(r"charting_library"))
            if frame is not None:
                return frame
            self.page.wait_for_timeout(250)
        return None

    def tradingview_body_text(self) -> str:
        frame = self.tradingview_frame()
        if frame is None:
            return ""
        try:
            return frame.locator("body").inner_text(timeout=10_000).strip()
        except Exception:
            return ""

    def tradingview_chart_has_non_blank_canvas(self) -> bool:
        frame = self.tradingview_frame()
        if frame is None:
            return False
        return bool(
            frame.evaluate(
                """
                () => {
                    const canvases = Array.from(document.querySelectorAll('canvas'));
                    return canvases.some((canvas) => {
                        if (!canvas.width || !canvas.height) return false;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return false;
                        const width = Math.max(1, Math.min(canvas.width, 64));
                        const height = Math.max(1, Math.min(canvas.height, 64));
                        const image = ctx.getImageData(0, 0, width, height).data;
                        let colored = 0;
                        for (let i = 0; i < image.length; i += 4) {
                            const alpha = image[i + 3];
                            const r = image[i];
                            const g = image[i + 1];
                            const b = image[i + 2];
                            if (alpha > 0 && !(r > 245 && g > 245 && b > 245)) {
                                colored += 1;
                            }
                        }
                        return colored > 100;
                    });
                }
                """
            )
        )

    def tradingview_has_date_range(self) -> bool:
        return "Date Range" in self.tradingview_body_text()

    def tradingview_symbol(self) -> str:
        body_match = re.search(r"\b([A-Z]{3,}USDT)\b", self.tradingview_body_text())
        if body_match:
            return body_match.group(1)

        iframe_src = self.page.locator("iframe[name^='tradingview_']").first.get_attribute("src") or ""
        src_match = re.search(r"symbol=([A-Z0-9]+)", iframe_src)
        if src_match:
            return src_match.group(1)

        try:
            first_row = self.first_deals_row()
        except Exception:
            return ""
        pair = first_row[1].replace("/", "").strip()
        return pair

    def tradingview_timeframe(self) -> str:
        body_match = re.search(r"\b(\d+[mhHdD])\b", self.tradingview_body_text())
        if body_match:
            return body_match.group(1)

        iframe_src = self.page.locator("iframe[name^='tradingview_']").first.get_attribute("src") or ""
        src_match = re.search(r"interval=(\d+)", iframe_src)
        if src_match:
            interval = src_match.group(1)
            interval_map = {"60": "1h", "240": "4h", "1440": "1D"}
            return interval_map.get(interval, interval)

        body_text = self._page_text()
        body_match = re.search(r"\b(\d+[mhHdD])\b", body_text)
        return body_match.group(1) if body_match else ""

    def tradingview_ohlc_summary(self) -> str:
        match = re.search(r"(O.+?C.+?\))", self.tradingview_body_text(), re.S)
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

    def deals_table_headers(self) -> list[str]:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            for table in self._tables_payload():
                flat_cells = [cell for row in table for cell in row]
                if {"Strategy", "Pair", "Profit", "Volumes", "Status", "Update"}.issubset(set(flat_cells)):
                    return flat_cells[:7]
            self.page.wait_for_timeout(250)
        return []

    def deals_table_rows(self) -> list[list[str]]:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            for table in self._tables_payload():
                flat_text = " ".join(cell for row in table for cell in row)
                if re.search(r"\bACTIVE\b|\bCOMPLETED\b", flat_text):
                    rows = [row for row in table if len(row) >= 7]
                    if rows:
                        return rows
            self.page.wait_for_timeout(250)
        return []

    def _tables_payload(self) -> list[list[list[str]]]:
        return self.page.evaluate(
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

    def first_deals_row(self) -> list[str]:
        rows = self.deals_table_rows()
        if not rows:
            raise AssertionError("Expected at least one deal row in the table.")
        return rows[0]

    def pagination_root(self) -> Locator:
        return self.page.locator(".el-pagination").first

    def pagination_page_numbers(self) -> list[str]:
        return [
            value.strip()
            for value in self.pagination_root().locator(".el-pager .number").all_inner_texts()
            if value.strip()
        ]

    def has_multiple_deal_pages(self) -> bool:
        numbers = self.pagination_page_numbers()
        return len(numbers) > 1

    def is_pagination_prev_disabled(self) -> bool:
        class_name = self.pagination_root().locator(".btn-prev").get_attribute("class") or ""
        return "disabled" in class_name

    def is_pagination_next_disabled(self) -> bool:
        class_name = self.pagination_root().locator(".btn-next").get_attribute("class") or ""
        return "disabled" in class_name

    def click_pagination_next(self) -> float:
        return self._paginate(self.pagination_root().locator(".btn-next").first)

    def click_pagination_prev(self) -> float:
        return self._paginate(self.pagination_root().locator(".btn-prev").first)

    def _paginate(self, target: Locator) -> float:
        before = self.first_deals_row()
        started_at = time.perf_counter()
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_function(
            """
            (previousRow) => {
                const tables = Array.from(document.querySelectorAll('table'));
                const table = tables[2];
                if (!table) return false;
                const firstRow = table.querySelector('tr');
                if (!firstRow) return false;
                const current = Array.from(firstRow.querySelectorAll('td'))
                    .map((cell) => (cell.innerText || '').replace(/\\s+/g, ' ').trim())
                    .filter(Boolean);
                return JSON.stringify(current) !== JSON.stringify(previousRow);
            }
            """,
            before,
            timeout=10_000,
        )
        duration_sec = time.perf_counter() - started_at
        allure.attach(f"{duration_sec:.2f} sec", "deals_table_pagination_duration", allure.attachment_type.TEXT)
        return duration_sec

    def click_copy_as_authenticated_user(self) -> str:
        with allure.step("Click COPY as an authenticated user and classify the outcome"):
            self._assert_target_actionable(self.copy_button())
            self._click_target(self.copy_button())
            self.page.wait_for_timeout(2_500)
            page_text = self._page_text()
            if re.search(r"You can.?t launch more strategies according to limits of your current subscription plan", page_text, re.I):
                return "membership_limit"
            if re.search(r"You have successfully purchased", page_text, re.I) or re.search(r"/dashboard/bot/list", self.page.url):
                return "copied"
            return "unknown"

    def fetch_public_json(self, path: str) -> Any:
        with allure.step(f"Fetch public API data for '{path}'"):
            response = self.page.context.request.get(f"https://api.gt-protocol.io{path}")
            assert response.ok, f"Expected 2xx from public API, got {response.status} for {path}"
            return response.json()

    def deals_api_payload(self, page_number: int = 1, page_size: int = 10) -> Any:
        return self.fetch_public_json(
            f"/api/v1/public/bot/{self.bot_id()}/deals?page_number={page_number}&page_size={page_size}"
        )

    def orders_api_payload(self) -> Any:
        return self.fetch_public_json(f"/api/v1/public/bot/{self.bot_id()}/orders")

    def top_trader_chart_payload(self) -> Any:
        return self.fetch_public_json(f"/api/v1/public/top_bots/{self.bot_id()}/chart?page_size=365&page_number=1")
