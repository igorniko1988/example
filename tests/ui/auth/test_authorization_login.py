import allure
import pytest

from src.pages.auth_page import AuthPage


@allure.feature("Authorization")
@allure.story("Login")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Authorization: valid credentials open the dashboard")
@pytest.mark.smoke
def test_login_with_env_credentials(page, base_url, auth_email, auth_password) -> None:
    auth = AuthPage(page, base_url)
    auth.login(auth_email, auth_password)
    auth.assert_redirected_to_dashboard()
    auth.assert_dashboard_shell_visible()


@allure.feature("Authorization")
@allure.story("Protected Page Access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Authorization: authenticated user can open the Profile page")
@pytest.mark.smoke
def test_authenticated_user_can_open_profile_page(page, base_url, auth_email, auth_password) -> None:
    auth = AuthPage(page, base_url)
    auth.login(auth_email, auth_password)
    auth.open_protected_profile_page()
    auth.assert_profile_page_opened_for_authenticated_user()
