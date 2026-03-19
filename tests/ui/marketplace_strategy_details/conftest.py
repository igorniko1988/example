import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.marketplace_strategy_details_page import MarketplaceStrategyDetailsPage


@pytest.fixture
def strategy_details_page(page, base_url) -> MarketplaceStrategyDetailsPage:
    with allure.step("Open Marketplace strategy details page for unauthenticated user"):
        details = MarketplaceStrategyDetailsPage(page, base_url)
        details.open_first_strategy_details()
        return details


@pytest.fixture
def logged_in_strategy_details_page(browser, base_url, strategy_details_auth_storage_state_path) -> MarketplaceStrategyDetailsPage:
    with allure.step("Open Marketplace strategy details page in a fresh authenticated browser context"):
        context = _new_authenticated_context(browser, strategy_details_auth_storage_state_path)
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            details = MarketplaceStrategyDetailsPage(page, base_url)
            details.open_first_strategy_details()
            yield details
        finally:
            page.close()
            context.close()


@pytest.fixture(scope="session")
def strategy_details_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("marketplace-strategy-details-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create Marketplace strategy details authenticated storage state"):
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
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
