import allure
import pytest
from playwright.sync_api import Browser

from src.pages.auth_page import AuthPage
from src.pages.membership_page import MembershipPage


@pytest.fixture
def logged_in_membership_page(browser, base_url, membership_auth_storage_state_path) -> MembershipPage:
    with allure.step("Open Membership page in a fresh authenticated browser context"):
        context = _new_authenticated_context(browser, membership_auth_storage_state_path)
        page = context.new_page()
        page.set_default_timeout(20_000)
        try:
            membership = MembershipPage(page, base_url)
            membership.open()
            yield membership
        finally:
            page.close()
            context.close()


@pytest.fixture(scope="session")
def membership_auth_storage_state_path(
    browser: Browser,
    base_url: str,
    auth_email: str,
    auth_password: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    state_dir = tmp_path_factory.mktemp("membership-auth")
    state_path = state_dir / "storage-state.json"

    with allure.step("Create Membership authenticated storage state"):
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
