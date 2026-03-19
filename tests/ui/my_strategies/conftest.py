import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.my_strategies_page import MyStrategiesPage


@pytest.fixture
def my_strategies_page(page, base_url) -> MyStrategiesPage:
    with allure.step("Open My Strategies for guest user"):
        current = MyStrategiesPage(page, base_url)
        current.open()
        return current


@pytest.fixture
def logged_in_my_strategies_page(browser, base_url, my_strategies_auth_storage_state_path) -> MyStrategiesPage:
    with allure.step("Open My Strategies in a fresh authenticated browser context"):
        context = _new_authenticated_context(browser, my_strategies_auth_storage_state_path)
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            current = MyStrategiesPage(page, base_url)
            current.open()
            yield current
        finally:
            page.close()
            context.close()


@pytest.fixture(scope="session")
def my_strategies_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("my-strategies-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create My Strategies authenticated storage state"):
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
