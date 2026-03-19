import re
import time
from urllib.parse import urljoin, urlparse

import allure
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, expect

from src.utils.allure_helpers import attach_expected_actual


class MarketplacePage:
    MARKETPLACE_PATH = "/dashboard/bots-marketplace"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        with allure.step("Open the Marketplace page"):
            self.page.goto(f"{self.base_url}{self.MARKETPLACE_PATH}", wait_until="domcontentloaded")
        with allure.step("Wait for Marketplace content to become visible"):
            expect(self.page.get_by_role("heading", name=re.compile(r"TOP profitable strategies of the month", re.I))).to_be_visible(timeout=30_000)
            expect(self.page.get_by_role("button", name=re.compile("details", re.I)).first).to_be_visible(timeout=30_000)

    def assert_loaded_without_errors(self) -> None:
        with allure.step("Verify the Marketplace page shell is visible"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/bots-marketplace"), timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(
                re.compile(r"TOP profitable strategies of the month|GT AI Backtest", re.I),
                timeout=30_000,
            )

    def assert_page_title(self) -> None:
        with allure.step("Verify the browser title is 'Dashboard | GT App'"):
            expect(self.page).to_have_title(re.compile(r"Dashboard \| GT App"))

    def assert_limited_time_offer_timer_format_when_present(self) -> None:
        with allure.step("Verify the limited-time offer timer format when the banner is shown"):
            body_text = self.page.locator("body").inner_text(timeout=10_000)
            if not re.search(r"Limited time offer", body_text, re.I):
                allure.attach(
                    "Limited time offer banner is not present in current session state.",
                    "limited_time_offer_absent",
                    allure.attachment_type.TEXT,
                )
                return
            timer_match = re.search(r"\b\d{2}:\d{2}:\d{2}:\d{2}\b", body_text)
            assert timer_match, body_text
            timer_text = timer_match.group(0)
            attach_expected_actual("Timer matches 00:00:00:00 format", f"actual timer: {timer_text}")
            assert re.fullmatch(r"\d{2}:\d{2}:\d{2}:\d{2}", timer_text), timer_text

    def assert_backtest_banner_copy(self) -> None:
        with allure.step("Verify the GT AI Backtest banner and marketing copy are shown"):
            expect(self.backtest_banner()).to_be_visible(timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(
                re.compile(r"The most intelligent backtest ever\.\s*Optimise 1000\+ strategies in less than 1 minute", re.I),
                timeout=30_000,
            )

    def assert_footer_shell(self) -> None:
        with allure.step("Verify footer links and copyright are visible"):
            expect(self.footer_support_link()).to_be_visible()
            expect(self.footer_terms_link()).to_be_visible()
            expect(self.footer_privacy_link()).to_be_visible()
            expect(self.footer_copyright()).to_be_visible()

    def sidebar_item(self, label: str) -> Locator:
        return self.ensure_sidebar_item_visible(label)

    def header_item(self, label: str) -> Locator:
        candidates = [
            self.page.locator(
                "xpath=//*[normalize-space(text())="
                f"'{label}']/ancestor::*[self::a or self::button or self::div][1]"
            ).first,
            self.page.get_by_role("link", name=re.compile(rf"^{re.escape(label)}$", re.I)).first,
            self.page.get_by_role("button", name=re.compile(rf"^{re.escape(label)}$", re.I)).first,
            self.page.locator(f"text=/{re.escape(label)}/i").first,
        ]
        for candidate in candidates:
            if candidate.count() == 0:
                continue
            try:
                if candidate.is_visible(timeout=2_000):
                    return candidate
            except Exception:
                continue
        return self.page.locator("xpath=/html[false()]")

    def assert_header_item_visible(self, label: str) -> Locator:
        with allure.step(f"Verify the '{label}' header control is visible"):
            target = self.header_item(label)
            expect(target).to_be_visible(timeout=10_000)
            return target

    def top_heading(self) -> Locator:
        return self.page.get_by_role("heading", name=re.compile(r"TOP profitable strategies of the month", re.I)).first

    def limited_time_offer_banner(self) -> Locator:
        return self.page.locator(
            "xpath=//*[self::div or self::span or self::p][contains(normalize-space(.), 'Limited time offer')]"
        ).filter(has=self.limited_time_offer_timer()).first

    def limited_time_offer_timer(self) -> Locator:
        return self.page.locator("text=/\\d{2}:\\d{2}:\\d{2}:\\d{2}/").first

    def backtest_banner(self) -> Locator:
        return self.page.get_by_role("heading", name=re.compile(r"GT AI Backtest", re.I)).first

    def backtest_cta(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"TRY IT NOW", re.I)).first

    def strategy_card_count(self) -> int:
        return self.page.get_by_role("button", name=re.compile(r"^Details$", re.I)).count()

    def nth_strategy_card(self, index: int) -> Locator:
        details_button = self.page.get_by_role("button", name=re.compile(r"^Details$", re.I)).nth(index)
        return details_button.locator(
            "xpath=ancestor::*[self::div or self::section or self::article]"
            "[.//button[normalize-space()='Copy']"
            " and .//button[normalize-space()='Details']"
            " and .//*[contains(normalize-space(.), 'Made by')]"
            " and .//*[contains(normalize-space(.), 'APY')]"
            " and .//*[contains(normalize-space(.), 'Risk')]"
            " and .//*[contains(normalize-space(.), 'Min. Balance')]][1]"
        )

    def first_strategy_card(self) -> Locator:
        return self.nth_strategy_card(0)

    def footer_support_link(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"^support$", re.I)).first

    def footer_terms_link(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"^Terms$", re.I)).first

    def footer_privacy_link(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"^Privacy Policy$", re.I)).first

    def footer_copyright(self) -> Locator:
        return self.page.locator("text=/©\\s*2026\\s*GT App/i").first

    def ensure_sidebar_item_visible(self, label: str) -> Locator:
        target = self.page.locator(f"text={label}").first
        if target.is_visible():
            return target

        if label in {"TOP Traders", "My Strategies", "Backtest", "Deals history"}:
            self.page.locator("text=Trading").first.click(force=True)
        if label in {"Exchange accounts", "Profile & Telegram", "Memberships"}:
            self.page.locator("text=Account").first.click(force=True)

        expect(target).to_be_visible(timeout=10_000)
        return target

    def click_and_capture_destination(self, target: Locator) -> tuple[str, str]:
        href = target.get_attribute("href")
        target_attr = (target.get_attribute("target") or "").strip().lower()
        origin_url = self.page.url
        navigation_mode = self._expected_navigation_mode(href, target_attr)

        self._assert_target_actionable(target)

        if navigation_mode in {"popup", "either"}:
            pages_before = len(self.page.context.pages)
            self._click_target(target)
            popup = self._wait_for_new_page(pages_before, timeout_ms=5_000)

            if popup is not None:
                try:
                    popup.wait_for_load_state("domcontentloaded", timeout=10_000)
                except Exception:
                    pass
                destination = popup.url
                popup.close()
                return destination, "popup"

            if navigation_mode == "popup":
                destination_hint = urljoin(origin_url, href) if href else "n/a"
                raise AssertionError(
                    f"Click did not open a popup/new page. href={destination_hint} current_url={self.page.url}"
                )

        if navigation_mode != "either":
            self._click_target(target)
        try:
            self.page.wait_for_url(
                lambda current_url: current_url != origin_url,
                timeout=10_000,
            )
            return self.page.url, "same_tab"
        except PlaywrightTimeoutError as error:
            if navigation_mode == "either":
                return self.page.url, "same_page"
            destination_hint = urljoin(origin_url, href) if href else "n/a"
            raise AssertionError(
                "Click did not trigger same-tab navigation. "
                f"expected_mode={navigation_mode} href={destination_hint} current_url={self.page.url}"
            ) from error

    def _click_target(self, target: Locator) -> None:
        try:
            target.click(timeout=10_000)
            return
        except Exception:
            pass

        try:
            target.click(timeout=10_000, force=True)
            return
        except Exception:
            pass

        handle = target.element_handle()
        if handle is None:
            raise AssertionError("Target element is not attached to the DOM for click execution.")
        self.page.evaluate("(el) => el.click()", handle)

    def _expected_navigation_mode(self, href: str | None, target_attr: str) -> str:
        if target_attr == "_blank":
            return "popup"
        if not href:
            return "either"

        parsed_href = urlparse(urljoin(self.page.url, href))
        parsed_base = urlparse(self.base_url)
        is_external = bool(parsed_href.scheme and parsed_href.netloc and parsed_href.netloc != parsed_base.netloc)
        return "popup" if is_external else "same_tab"

    def _wait_for_new_page(self, pages_before: int, timeout_ms: int) -> Page | None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            pages_after = self.page.context.pages
            if len(pages_after) > pages_before:
                return pages_after[-1]
            self.page.wait_for_timeout(100)
        return None

    def _assert_target_actionable(self, target: Locator) -> None:
        last_overlay_state: dict | None = None
        for _ in range(6):
            target.scroll_into_view_if_needed()
            expect(target).to_be_visible(timeout=10_000)

            is_enabled = True
            try:
                is_enabled = target.is_enabled(timeout=1_000)
            except Exception:
                is_enabled = True
            if not is_enabled:
                raise AssertionError("Target element is disabled and should not be clicked.")

            handle = target.element_handle()
            if handle is None:
                raise AssertionError("Target element is detached from the DOM before click.")

            overlay_state = self.page.evaluate(
                """
                (el) => {
                    const rect = el.getBoundingClientRect();
                    if (!rect || rect.width === 0 || rect.height === 0) {
                        return { actionable: false, reason: "zero-sized element" };
                    }

                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;
                    const topNode = document.elementFromPoint(x, y);
                    if (!topNode) {
                        return { actionable: false, reason: "no element at click point" };
                    }

                    const actionable =
                        topNode === el ||
                        el.contains(topNode) ||
                        topNode.contains(el) ||
                        !!topNode.closest('[role="dialog"] button, [role="dialog"] a');

                    return {
                        actionable,
                        reason: actionable ? "" : "click point is covered by another element",
                        topTag: topNode.tagName,
                        topText: (topNode.textContent || "").trim().slice(0, 120),
                    };
                }
                """,
                handle,
            )
            if overlay_state.get("actionable", False):
                return

            last_overlay_state = overlay_state
            top_text = (overlay_state.get("topText") or "").strip().lower()
            if "loading" in top_text:
                self._wait_for_loading_overlay_to_clear()
                continue
            self.page.wait_for_timeout(300)

        overlay_state = last_overlay_state or {}
        raise AssertionError(
            "Target element is not actionable for click: "
            f"{overlay_state.get('reason', 'unknown reason')} "
            f"(topTag={overlay_state.get('topTag', '')}, topText={overlay_state.get('topText', '')!r})"
        )

    def _wait_for_loading_overlay_to_clear(self, timeout_ms: int = 10_000) -> None:
        loading_candidates = [
            self.page.locator("text=/^Loading$/i").first,
            self.page.locator("text=/Loading/i").first,
        ]
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            visible = False
            for candidate in loading_candidates:
                try:
                    if candidate.count() > 0 and candidate.is_visible(timeout=200):
                        visible = True
                        break
                except Exception:
                    continue
            if not visible:
                return
            self.page.wait_for_timeout(300)

    def assert_redirect_destination(self, target: Locator, expected_url_pattern: str, step_name: str) -> tuple[str, str]:
        with allure.step(step_name):
            destination_url, mode = self.click_and_capture_destination(target)
            allure.attach(mode, "open_mode", allure.attachment_type.TEXT)
            allure.attach(destination_url, "destination_url", allure.attachment_type.TEXT)
            assert re.search(expected_url_pattern, destination_url), destination_url
            return destination_url, mode

    def assert_current_url(self, expected_url_pattern: str, step_name: str) -> None:
        with allure.step(step_name):
            expect(self.page).to_have_url(re.compile(expected_url_pattern), timeout=30_000)

    def click_strategy_button(self, card: Locator, label: str) -> None:
        with allure.step(f"Click '{label}' on the Marketplace strategy card"):
            button = card.get_by_role("button", name=re.compile(rf"^{re.escape(label)}$", re.I)).first
            self._assert_target_actionable(button)
            self._click_target(button)

    def get_card_text(self, card: Locator) -> str:
        return card.inner_text(timeout=10_000)

    def get_card_strategy_name(self, card: Locator) -> str:
        with allure.step("Read the strategy name from the Marketplace card"):
            text = self.get_card_text(card)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines:
                if re.fullmatch(r"TRENDING", line, re.I):
                    continue
                if re.fullmatch(r"FUTURES|SPOT|LONG|SHORT|COPY|DETAILS", line, re.I):
                    continue
                if re.fullmatch(r"Made by|APY|Lifetime|Risk|Min\. Balance", line, re.I):
                    continue
                return line
            raise AssertionError(f"Could not extract strategy name from marketplace card text: {text}")

    def card_avatar_image(self, card: Locator) -> Locator:
        return card.locator("img").nth(1) if card.locator("img").count() > 1 else card.locator("img").first

    def is_image_loaded(self, image: Locator) -> bool:
        handle = image.element_handle()
        if handle is None:
            return False
        return bool(
            self.page.evaluate(
                "(img) => Boolean(img && img.complete && img.naturalWidth > 0 && img.naturalHeight > 0)",
                handle,
            )
        )

    def card_has_loaded_image(self, card: Locator) -> bool:
        images = card.locator("img")
        for idx in range(images.count()):
            candidate = images.nth(idx)
            try:
                if self.is_image_loaded(candidate):
                    return True
            except Exception:
                continue
        return False

    def assert_backtest_new_badge_visible(self) -> None:
        with allure.step("Verify the sidebar shows Backtest with the NEW badge"):
            expect(self.page.locator("body")).to_contain_text(re.compile(r"Backtest\s*NEW|BacktestNEW", re.I))

    def assert_strategy_section_has_cards(self) -> int:
        with allure.step("Verify the top profitable strategies section is visible and not empty"):
            cards_count = self.strategy_card_count()
            expect(self.top_heading()).to_be_visible(timeout=30_000)
            assert cards_count > 0, "Expected at least one marketplace strategy card."
            return cards_count

    def assert_first_three_cards_are_trending(self) -> None:
        with allure.step("Verify the first three Marketplace cards are marked TRENDING"):
            cards_count = self.assert_strategy_section_has_cards()
            first_three = min(cards_count, 3)
            assert first_three == 3, "Expected at least three strategy cards to verify TRENDING badges."
            for idx in range(first_three):
                expect(self.nth_strategy_card(idx)).to_contain_text(re.compile(r"TRENDING", re.I))

    def assert_card_has_required_fields_and_actions(self, index: int) -> None:
        with allure.step(f"Verify Marketplace card #{index + 1} shows required details, avatar and actions"):
            card = self.nth_strategy_card(index)
            card_text = self.get_card_text(card)
            assert re.search(r"\b(FUTURES|SPOT)\b", card_text, re.I), card_text
            assert re.search(r"\b(Long|Short)\b", card_text, re.I), card_text
            assert re.search(r"Made by", card_text), card_text
            assert re.search(r"\bAPY\b", card_text), card_text
            assert re.search(r"\bLifetime\b", card_text), card_text
            assert re.search(r"\bRisk\b", card_text), card_text
            assert re.search(r"Min\.\s*Balance", card_text), card_text
            assert re.search(r"\bUSDT\b", card_text), card_text

            assert self.card_has_loaded_image(card), f"No loaded image found for card {index + 1}"

            copy_button = card.get_by_role("button", name=re.compile(r"^Copy$", re.I)).first
            details_button = card.get_by_role("button", name=re.compile(r"^Details$", re.I)).first
            expect(copy_button).to_be_enabled(timeout=10_000)
            expect(details_button).to_be_enabled(timeout=10_000)

    def assert_copy_membership_limit_feedback(self, strategy_name: str) -> None:
        with allure.step("Verify the copied top strategy appears in subscription history and shows membership feedback"):
            expect(self.page.locator("body")).to_contain_text(
                re.compile(r"You can.?t launch more strategies according to limits of your current subscription plan", re.I),
                timeout=30_000,
            )
            expect(self.page.locator("body")).to_contain_text(re.compile(r"Your subscriptions history", re.I), timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(re.escape(strategy_name), re.I), timeout=30_000)

    def assert_unauthenticated_copy_redirected_to_register(self) -> None:
        self.assert_current_url(r"/auth\?tab=register", "Verify unauthenticated Copy redirects to registration page")

    def assert_strategy_details_page_opened(self) -> None:
        self.assert_current_url(
            r"/dashboard/bots-marketplace/statistics/",
            "Verify marketplace strategy details page is opened",
        )
