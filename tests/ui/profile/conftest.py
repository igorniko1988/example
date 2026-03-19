import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.profile_page import ProfilePage


@pytest.fixture(scope="session")
def profile_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("profile-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create Profile session-level authenticated storage state"):
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


@pytest.fixture
def logged_in_profile_page(browser: Browser, base_url: str, profile_auth_storage_state_path: str) -> ProfilePage:
    with allure.step("Open Profile page in a fresh authenticated browser context"):
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            storage_state=profile_auth_storage_state_path,
        )
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            profile = ProfilePage(page, base_url)
            profile.open()
            yield profile
        finally:
            page.close()
            context.close()
