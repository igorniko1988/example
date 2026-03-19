import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Profile")
@allure.story("Identity And Password")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: UID is visible and non-empty")
def test_uid_is_visible_and_numeric(logged_in_profile_page) -> None:
    assert logged_in_profile_page.uid_value().isdigit()


@allure.feature("Profile")
@allure.story("Identity And Password")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: email is visible and non-empty")
def test_email_is_visible_and_non_empty(logged_in_profile_page) -> None:
    assert "@" in logged_in_profile_page.email_value()


@allure.feature("Profile")
@allure.story("Identity And Password")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: password fields are visible and accept input")
@pytest.mark.parametrize("placeholder", ["Current Password", "New Password", "Confirm Password"])
def test_password_fields_accept_input(logged_in_profile_page, placeholder: str) -> None:
    field = logged_in_profile_page.password_input(placeholder)
    expect(field).to_be_visible()
    field.fill("ExamplePassword1!")
    expect(field).to_have_value("ExamplePassword1!")


@allure.feature("Profile")
@allure.story("Identity And Password")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: password visibility toggle is present for each password field and changes input type")
@pytest.mark.parametrize("placeholder", ["Current Password", "New Password", "Confirm Password"])
def test_password_visibility_toggle_changes_input_type(logged_in_profile_page, placeholder: str) -> None:
    field = logged_in_profile_page.password_input(placeholder)
    toggle = logged_in_profile_page.password_visibility_toggle(placeholder)

    expect(toggle).to_be_visible()
    assert field.get_attribute("type") == "password"
    toggle.click()
    expect(field).to_have_attribute("type", "text")
    toggle.click()
    expect(field).to_have_attribute("type", "password")


@allure.feature("Profile")
@allure.story("Identity And Password")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Save Password' button is visible and enabled")
def test_save_password_button_is_visible_and_clickable(logged_in_profile_page) -> None:
    button = logged_in_profile_page.page.get_by_role("button", name="Save Password")
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Profile")
@allure.story("Identity And Password Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: required-field validation is shown for empty password fields")
def test_password_form_required_validation(logged_in_profile_page) -> None:
    logged_in_profile_page.fill_password_form()
    logged_in_profile_page.click_save_password()
    expect(logged_in_profile_page.required_password_errors()).to_have_count(3)


@allure.feature("Profile")
@allure.story("Identity And Password Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: mismatched new and confirm passwords show a validation error")
def test_password_form_mismatch_validation(logged_in_profile_page, auth_password: str) -> None:
    logged_in_profile_page.fill_password_form(
        current_password=auth_password,
        new_password="ExamplePassword1!",
        confirm_password="DifferentPassword1!",
    )
    logged_in_profile_page.click_save_password()
    logged_in_profile_page.assert_password_validation_message(r"passwords?.*(does not match|match)")


@allure.feature("Profile")
@allure.story("Identity And Password Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: too-short new password shows a password policy validation error")
def test_password_form_short_password_validation(logged_in_profile_page, auth_password: str) -> None:
    logged_in_profile_page.fill_password_form(
        current_password=auth_password,
        new_password="123",
        confirm_password="123",
    )
    logged_in_profile_page.click_save_password()
    logged_in_profile_page.assert_password_validation_message(r"(minimum|min\.?|least|length|8)")
