import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.exchange_connect_pages import (
    ConnectBinancePage,
    ConnectHyperliquidPage,
    ExchangeAccountsOverviewPage,
)


@pytest.fixture(scope="session")
def exchange_pages_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("exchange-pages-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create authenticated storage state for exchange pages"):
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            AuthPage(page, base_url).login(auth_email, auth_password)
            context.storage_state(path=str(state_path))
        finally:
            page.close()
            context.close()

    return str(state_path)


def _new_authenticated_context(browser: Browser, storage_state_path: str):
    return browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="en-US",
        storage_state=storage_state_path,
    )


@pytest.fixture
def exchange_overview_page(browser, base_url, exchange_pages_auth_storage_state_path) -> ExchangeAccountsOverviewPage:
    context = _new_authenticated_context(browser, exchange_pages_auth_storage_state_path)
    page = context.new_page()
    page.set_default_timeout(20_000)
    try:
        overview = ExchangeAccountsOverviewPage(page, base_url)
        overview.open()
        yield overview
    finally:
        page.close()
        context.close()


@pytest.fixture
def connect_binance_page(browser, base_url, exchange_pages_auth_storage_state_path) -> ConnectBinancePage:
    context = _new_authenticated_context(browser, exchange_pages_auth_storage_state_path)
    page = context.new_page()
    page.set_default_timeout(20_000)
    try:
        connect_page = ConnectBinancePage(page, base_url)
        connect_page.open()
        yield connect_page
    finally:
        page.close()
        context.close()


@pytest.fixture
def connect_hyperliquid_page(browser, base_url, exchange_pages_auth_storage_state_path) -> ConnectHyperliquidPage:
    context = _new_authenticated_context(browser, exchange_pages_auth_storage_state_path)
    page = context.new_page()
    page.set_default_timeout(20_000)
    try:
        connect_page = ConnectHyperliquidPage(page, base_url)
        connect_page.open()
        yield connect_page
    finally:
        page.close()
        context.close()

