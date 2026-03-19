import re
import time
from typing import Any

import allure
from playwright.sync_api import Locator, Page, expect

from src.pages.marketplace_page import MarketplacePage


class MyStrategiesPage(MarketplacePage):
    PATH = "/dashboard/bot/list"

    def open(self) -> None:
        with allure.step("Open the My Strategies page"):
            self.page.goto(f"{self.base_url}{self.PATH}", wait_until="domcontentloaded")
        self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        with allure.step("Wait for My Strategies content to become visible"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
            expect(self.page.get_by_role("heading", name=re.compile(r"^My Strategies$", re.I))).to_be_visible(timeout=30_000)
            expect(self.page.locator("body")).to_contain_text(re.compile(r"Strategies|Quick Presets|Demo Trading", re.I), timeout=30_000)

    def measure_warm_load(self) -> float:
        with allure.step("Measure warm load time for My Strategies"):
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
            allure.attach(f"{duration_sec:.2f} sec", "my_strategies_warm_load_duration", allure.attachment_type.TEXT)
            return duration_sec

    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name=re.compile(r"^My Strategies$", re.I)).first

    def section_header(self, name: str) -> Locator:
        return self.page.locator(".el-collapse-item__header", has_text=re.compile(rf"^{re.escape(name)}$", re.I)).first

    def section_expanded(self, name: str) -> bool:
        class_name = self.section_header(name).get_attribute("class") or ""
        return "is-active" in class_name

    def toggle_section(self, name: str) -> None:
        header = self.section_header(name)
        self._assert_target_actionable(header)
        self._click_target(header)
        self.page.wait_for_timeout(500)

    def top_create_button(self, label: str) -> Locator:
        return self.page.locator(f"text={label}").first

    def click_top_create_button(self, label: str) -> None:
        target = self.top_create_button(label)
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_timeout(800)

    def page_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def cards_payload(self) -> list[dict[str, Any]]:
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.bot-card__wrapper')).map((el, i) => ({
                i,
                text: (el.innerText || '').replace(/\\s+/g, ' ').trim(),
                className: el.className,
                canvases: el.querySelectorAll('canvas').length,
                buttons: Array.from(el.querySelectorAll('button')).map((b) => ({
                    text: (b.innerText || '').replace(/\\s+/g, ' ').trim(),
                    disabled: Boolean(b.disabled),
                    className: b.className || ''
                })).filter((b) => b.text),
                inputs: Array.from(el.querySelectorAll('input')).map((inp) => ({
                    placeholder: inp.placeholder || '',
                    value: inp.value || '',
                    disabled: Boolean(inp.disabled),
                    className: inp.className || ''
                }))
            }))
            """
        )

    def copy_cards_payload(self) -> list[dict[str, Any]]:
        return [card for card in self.cards_payload() if "Made by " in card["text"]]

    def preset_cards_payload(self) -> list[dict[str, Any]]:
        return [card for card in self.cards_payload() if "Backtested APY" in card["text"]]

    def demo_cards_payload(self) -> list[dict[str, Any]]:
        return [card for card in self.cards_payload() if "Demo Strategy" in card["text"]]

    def personal_cards_payload(self) -> list[dict[str, Any]]:
        return [
            card
            for card in self.cards_payload()
            if "Demo Strategy" not in card["text"] and "Made by " not in card["text"] and "Backtested APY" not in card["text"]
        ]

    def launch_personal_cards_payload(self) -> list[dict[str, Any]]:
        return [
            card
            for card in self.personal_cards_payload()
            if any(button["text"].lower() == "launch" for button in card["buttons"])
        ]

    def pause_personal_cards_payload(self) -> list[dict[str, Any]]:
        return [
            card
            for card in self.personal_cards_payload()
            if any(button["text"].lower() == "pause" for button in card["buttons"])
        ]

    def first_copy_card(self) -> Locator:
        return self.page.locator(".bot-card__wrapper", has_text=re.compile(r"Made by", re.I)).first

    def copy_card_exchange_input(self) -> Locator:
        return self.first_copy_card().locator("input[placeholder='Connect exchange']").first

    def copy_card_create_button(self) -> Locator:
        return self.first_copy_card().get_by_role("button", name=re.compile(r"^Create Strategy$", re.I)).first

    def copy_card_delete_link(self) -> Locator:
        return self.first_copy_card().locator("text=Delete Strategy").first

    def open_copy_exchange_dropdown(self) -> None:
        target = self.copy_card_exchange_input()
        self._assert_target_actionable(target)
        target.click()
        self.page.wait_for_timeout(800)

    def open_delete_confirmation_from_copy_card(self) -> None:
        target = self.copy_card_delete_link()
        self._assert_target_actionable(target)
        self._click_target(target)
        expect(self.page.get_by_role("dialog")).to_be_visible(timeout=10_000)

    def dismiss_delete_confirmation(self) -> None:
        dialog = self.page.get_by_role("dialog").first
        no_button = dialog.locator("text=No").first
        if no_button.count() > 0 and no_button.is_visible():
            no_button.click()
            self.page.wait_for_timeout(500)

    def preset_card(self, index: int) -> Locator:
        return self.page.locator(".bot-card-preset").nth(index)

    def preset_amount_option(self, card_index: int, label: str) -> Locator:
        return self.preset_card(card_index).locator(".bot-card-preset__preset-amount", has_text=label).first

    def click_preset_amount_option(self, card_index: int, label: str) -> None:
        target = self.preset_amount_option(card_index, label)
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_timeout(400)

    def preset_amount_option_selected(self, card_index: int, label: str) -> bool:
        class_name = self.preset_amount_option(card_index, label).get_attribute("class") or ""
        return "selected" in class_name

    def preset_amount_input(self, card_index: int) -> Locator:
        return self.preset_card(card_index).locator("input[placeholder='Enter Amount...']").first

    def try_fill_preset_amount_input(self, card_index: int, value: str) -> str:
        field = self.preset_amount_input(card_index)
        field.click()
        field.fill(value)
        self.page.wait_for_timeout(300)
        return field.input_value()

    def preset_exchange_input(self, card_index: int) -> Locator:
        return self.preset_card(card_index).locator("input[placeholder='Connect exchange']").first

    def open_preset_exchange_dropdown(self, card_index: int) -> None:
        target = self.preset_exchange_input(card_index)
        self._assert_target_actionable(target)
        target.click()
        self.page.wait_for_timeout(800)

    def preset_create_button(self, card_index: int) -> Locator:
        return self.preset_card(card_index).get_by_role("button", name=re.compile(r"^Create$", re.I)).first

    def preset_exchange_prompt_present(self) -> bool:
        return "Please connect a new exchange." in self.page_text() or "Please select an exchange to create the strategy." in self.page_text()

    def guest_amount_click_redirects(self) -> bool:
        target = self.page.locator(".bot-card-preset__preset-amount").first
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_timeout(800)
        return bool(re.search(r"/auth\?tab=register", self.page.url))

    def guest_amount_input_click_redirects(self) -> bool:
        target = self.page.locator("input[placeholder='Enter Amount...']").first
        self._assert_target_actionable(target)
        target.click()
        self.page.wait_for_timeout(800)
        return bool(re.search(r"/auth\?tab=register", self.page.url))

    def demo_card(self, index: int) -> Locator:
        return self.page.locator(".bot-card__wrapper", has_text=re.compile(r"Demo Strategy", re.I)).nth(index)

    def demo_launch_demo_button(self, index: int) -> Locator:
        return self.demo_card(index).locator("text=LAUNCH DEMO").first

    def demo_launch_real_button(self, index: int) -> Locator:
        return self.demo_card(index).locator("text=LAUNCH REAL").first

    def demo_delete_link(self, index: int) -> Locator:
        return self.demo_card(index).locator("text=Delete Strategy").first

    def click_demo_launch_real(self, index: int) -> None:
        target = self.demo_launch_real_button(index)
        self._assert_target_actionable(target)
        self._click_target(target)
        self.page.wait_for_timeout(800)

    def footer_copyright(self) -> Locator:
        return self.page.locator("text=/©\\s*2026\\s*GT App/i").first
