import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.futures_strategy_page import FuturesStrategyPage
from src.pages.marketplace_page import MarketplacePage


@pytest.fixture
def marketplace_page(page, base_url) -> MarketplacePage:
    with allure.step("Open Marketplace page for unauthenticated user"):
        marketplace = MarketplacePage(page, base_url)
        marketplace.open()
        return marketplace


@pytest.fixture
def logged_in_marketplace_page(browser, base_url, marketplace_auth_storage_state_path) -> MarketplacePage:
    with allure.step("Open Marketplace page in a fresh authenticated browser context"):
        context = _new_authenticated_context(browser, marketplace_auth_storage_state_path)
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            marketplace = MarketplacePage(page, base_url)
            marketplace.open()
            yield marketplace
        finally:
            page.close()
            context.close()


@pytest.fixture
def copied_marketplace_strategy_names(browser, base_url, marketplace_auth_storage_state_path) -> list[str]:
    created_names: list[str] = []
    yield created_names

    if not created_names:
        return

    with allure.step("Prepare authenticated session for Marketplace strategy cleanup"):
        context = _new_authenticated_context(browser, marketplace_auth_storage_state_path)
        page = context.new_page()
        page.set_default_timeout(20_000)

    try:
        cleanup = FuturesStrategyPage(page, base_url)
        for strategy_name in reversed(list(dict.fromkeys(created_names))):
            with allure.step(f"Cleanup copied Marketplace strategy '{strategy_name}' from My Strategies"):
                deleted = False
                for _ in range(3):
                    try:
                        deleted = cleanup.delete_top_strategy_from_list_if_exists(strategy_name)
                        if deleted:
                            break
                    except Exception:
                        pass
                    try:
                        deleted = cleanup.delete_futures_strategy_from_list_if_exists(strategy_name, strategy_id=None)
                        if deleted:
                            break
                    except Exception:
                        pass
                if not deleted:
                    allure.attach(
                        f"Strategy '{strategy_name}' was not deleted by cleanup fixture.",
                        "marketplace_cleanup_warning",
                        allure.attachment_type.TEXT,
                    )
    finally:
        page.close()
        context.close()


@pytest.fixture(scope="session")
def marketplace_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("marketplace-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create Marketplace session-level authenticated storage state"):
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
