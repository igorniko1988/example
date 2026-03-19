import re

import allure
from playwright.sync_api import Locator, Page, expect


class ExchangeAccountsOverviewPage:
    PATH = "/dashboard/exchange"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}{self.PATH}", wait_until="domcontentloaded")
        self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
        expect(self.page.get_by_text(re.compile(r"Connect exchange account", re.I)).first).to_be_visible(timeout=30_000)
        expect(self.page.get_by_role("button", name=re.compile(r"Connect Binance", re.I))).to_be_visible(timeout=30_000)
        self.page.wait_for_function(
            "() => !(document.body && document.body.innerText.includes('Loading'))",
            timeout=30_000,
        )

    def measure_warm_load(self) -> float:
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
        allure.attach(f"{duration_sec:.2f} sec", "exchange_overview_warm_load_duration", allure.attachment_type.TEXT)
        return duration_sec

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Connect exchange account", re.I)).first

    def banner(self) -> Locator:
        return self.page.get_by_text(
            re.compile(r"Your API keys cannot withdraw funds,?\s*only trading permissions", re.I)
        ).first

    def binance_card(self) -> Locator:
        return self.page.locator(".exchange-block-list__item").filter(has_text=re.compile(r"Connect Binance", re.I)).first

    def hyperliquid_card(self) -> Locator:
        return self.page.locator(".exchange-block-list__item").filter(has_text=re.compile(r"Connect Hyperliquid", re.I)).first

    def binance_logo(self) -> Locator:
        return self.page.locator("img[alt='Binance logo']").first

    def hyperliquid_logo(self) -> Locator:
        return self.page.locator("img[alt='Hyperliquid logo']").first

    def connect_binance_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"Connect Binance", re.I)).first

    def connect_hyperliquid_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"Connect Hyperliquid", re.I)).first

    def open_binance_form(self) -> None:
        self.connect_binance_button().click()
        expect(self.page).to_have_url(re.compile(r"/dashboard/connect-binance"), timeout=30_000)

    def open_hyperliquid_form(self) -> None:
        self.connect_hyperliquid_button().click()
        expect(self.page).to_have_url(re.compile(r"/dashboard/connect-hyperliquid"), timeout=30_000)

    def open_register_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"Register now", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup

    def open_hyperliquid_signup_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"set up new account", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup

    def connected_exchanges_heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Connected Exchanges", re.I)).first

    def has_connected_exchanges(self) -> bool:
        try:
            return self.connected_exchanges_heading().is_visible(timeout=1_000)
        except Exception:
            return False

    def connected_exchange_rows(self) -> list[str]:
        body = self.body_text()
        return [
            line.strip()
            for line in body.splitlines()
            if re.search(r".+\s*/\s*(Binance|Hyperliquid)\s*$", line.strip(), re.I)
        ]


class ConnectBinancePage:
    PATH = "/dashboard/connect-binance"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}{self.PATH}", wait_until="domcontentloaded")
        self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/dashboard/connect-binance"), timeout=30_000)
        expect(self.page.get_by_text(re.compile(r"Connect Binance API", re.I)).first).to_be_visible(timeout=30_000)
        expect(self.page.locator("input[name='bn-connection-name']")).to_be_visible(timeout=30_000)

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Connect Binance API", re.I)).first

    def logo(self) -> Locator:
        return self.page.locator(".exchange-header__logo").first

    def banner(self) -> Locator:
        return self.page.get_by_text(
            re.compile(r"Your API keys cannot withdraw funds,?\s*only trading permissions", re.I)
        ).first

    def back_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Back$", re.I)).first

    def one_click_heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Connect your Binance account in 1 click", re.I)).first

    def one_click_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"Connect Binance API and continue", re.I)).first

    def manual_heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Manual API Keys Setup", re.I)).first

    def connection_name_input(self) -> Locator:
        return self.page.locator("input[name='bn-connection-name']").first

    def api_key_input(self) -> Locator:
        return self.page.locator("input[name='bn-api-key']").first

    def api_secret_input(self) -> Locator:
        return self.page.locator("input[name='bn-api-secret']").first

    def connect_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"Connect to Exchange|Connecting\.\.\.", re.I)).first

    def eye_icons(self) -> Locator:
        return self.page.locator(".icon--eye-view")

    def open_guide_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"short video guide", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup

    def open_create_account_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"Create it now", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup


class ConnectHyperliquidPage:
    PATH = "/dashboard/connect-hyperliquid"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}{self.PATH}", wait_until="domcontentloaded")
        self.wait_until_loaded()

    def wait_until_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/dashboard/connect-hyperliquid"), timeout=30_000)
        expect(self.page.get_by_text(re.compile(r"Connect Hyperliquid API", re.I)).first).to_be_visible(timeout=30_000)
        expect(self.page.locator("input[name='hl-connection-name']")).to_be_visible(timeout=30_000)

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=10_000)

    def heading(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Connect Hyperliquid API", re.I)).first

    def logo(self) -> Locator:
        return self.page.locator(".exchange-header__logo").first

    def banner(self) -> Locator:
        return self.page.get_by_text(
            re.compile(r"Your API keys cannot withdraw funds,?\s*only trading permissions", re.I)
        ).first

    def back_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"^Back$", re.I)).first

    def connection_name_input(self) -> Locator:
        return self.page.locator("input[name='hl-connection-name']").first

    def private_key_input(self) -> Locator:
        return self.page.locator("input[name='hl-private-key']").first

    def connect_wallet_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"Connect wallet", re.I)).first

    def eye_icons(self) -> Locator:
        return self.page.locator(".icon--eye-view")

    def info_icons(self) -> Locator:
        return self.page.locator(".informer_label_wrp")

    def wallet_modal(self) -> Locator:
        return self.page.locator(".wallet-connect-wrapper").first

    def wallet_iframe(self) -> Locator:
        return self.page.locator("iframe[src*='walletconnect']").first

    def open_guide_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"Read step-by-step guide", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup

    def open_signup_popup(self) -> Page:
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name=re.compile(r"Set up a new Hyperliquid account", re.I)).click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=30_000)
        return popup
