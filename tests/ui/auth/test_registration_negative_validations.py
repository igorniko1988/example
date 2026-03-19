import allure
import pytest

from src.pages.auth_page import AuthPage


PASSWORD_RULE_TEXT = (
    "The password must be at least eight characters long and include letters, "
    "numbers and special characters"
)


@allure.feature("Registration")
@allure.story("Required Fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Registration: empty email and password show required field validation")
@pytest.mark.smoke
def test_registration_requires_email_and_password(page, base_url) -> None:
    auth = AuthPage(page, base_url)
    auth.open_register()
    auth.submit_register_form("", "")
    auth.assert_required_field_errors_visible()
    auth.assert_registration_page_is_still_open()


@allure.feature("Registration")
@allure.story("Email Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Registration: invalid email shows an email format validation error")
def test_registration_shows_invalid_email_error(page, base_url) -> None:
    auth = AuthPage(page, base_url)
    auth.open_register()
    auth.submit_register_form("abc", "Aa!23456")
    auth.assert_invalid_email_error_visible()
    auth.assert_registration_page_is_still_open()


@allure.feature("Registration")
@allure.story("Password Policy Validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("weak_password", ["12345", "passwordpassword", "Pass1234"])
def test_registration_shows_password_rules_error(page, base_url, weak_password: str) -> None:
    allure.dynamic.title(f"Registration: weak password '{weak_password}' shows password policy validation")
    auth = AuthPage(page, base_url)
    auth.open_register()
    auth.submit_register_form("abc@gmail.com", weak_password)
    auth.assert_password_rules_error_visible(PASSWORD_RULE_TEXT)
    auth.assert_registration_page_is_still_open()
