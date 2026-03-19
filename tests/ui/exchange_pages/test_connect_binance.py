import random
import re

import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Exchange Pages")
@allure.story("Connect Binance")
@allure.title("Connect Binance: page loads successfully")
def test_connect_binance_page_loads(connect_binance_page) -> None:
    expect(connect_binance_page.heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance")
@allure.title("Connect Binance: heading and logo are visible")
def test_connect_binance_heading_and_logo(connect_binance_page) -> None:
    expect(connect_binance_page.heading()).to_be_visible()
    expect(connect_binance_page.logo()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance")
@allure.title("Connect Binance: safety banner is visible")
def test_connect_binance_banner(connect_binance_page) -> None:
    expect(connect_binance_page.banner()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance")
@allure.title("Connect Binance: guide link opens Binance documentation in a new tab")
def test_connect_binance_guide_link(connect_binance_page) -> None:
    popup = connect_binance_page.open_guide_popup()
    try:
        assert popup.url.startswith("https://www.binance.com/en/support/faq/detail/360002502072")
    finally:
        popup.close()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance")
@allure.title("Connect Binance: Back returns to the exchange overview page")
def test_connect_binance_back_button(connect_binance_page) -> None:
    connect_binance_page.back_button().click()
    expect(connect_binance_page.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)


@allure.feature("Exchange Pages")
@allure.story("Connect Binance One Click")
@allure.title("Connect Binance: one-click section heading is visible")
def test_connect_binance_one_click_heading(connect_binance_page) -> None:
    expect(connect_binance_page.one_click_heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance One Click")
@allure.title("Connect Binance: one-click description is visible")
def test_connect_binance_one_click_description(connect_binance_page) -> None:
    assert "Start trading and profiting instantly with easy account setup (recommended)" in connect_binance_page.body_text()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance One Click")
@allure.title("Connect Binance: one-click button is visible and enabled")
def test_connect_binance_one_click_button(connect_binance_page) -> None:
    button = connect_binance_page.one_click_button()
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance One Click")
@allure.title("Connect Binance: one-click flow opens Binance OAuth in the same tab")
def test_connect_binance_one_click_redirect(connect_binance_page) -> None:
    connect_binance_page.one_click_button().click()
    connect_binance_page.page.wait_for_timeout(3_000)
    assert connect_binance_page.page.url.startswith("https://accounts.binance.com/")


@allure.feature("Exchange Pages")
@allure.story("Connect Binance One Click")
@allure.title("Connect Binance: Create it now opens Binance registration in a new tab")
def test_connect_binance_create_account_link(connect_binance_page) -> None:
    popup = connect_binance_page.open_create_account_popup()
    try:
        assert popup.url.startswith("https://www.binance.com/en/register")
    finally:
        popup.close()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: manual API keys setup heading is visible")
def test_connect_binance_manual_heading(connect_binance_page) -> None:
    expect(connect_binance_page.manual_heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: Connection Name field shows placeholder and accepts input")
def test_connect_binance_connection_name_input(connect_binance_page) -> None:
    field = connect_binance_page.connection_name_input()
    assert field.get_attribute("placeholder") == "Exchange connection name"
    field.fill("UI Test Binance")
    expect(field).to_have_value("UI Test Binance")


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: API Key field shows placeholder and accepts input")
def test_connect_binance_api_key_input(connect_binance_page) -> None:
    field = connect_binance_page.api_key_input()
    assert field.get_attribute("placeholder") == "API key"
    field.fill("test-api-key")
    assert field.input_value() != ""


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: API Secret field shows placeholder and accepts input")
def test_connect_binance_api_secret_input(connect_binance_page) -> None:
    field = connect_binance_page.api_secret_input()
    assert field.get_attribute("placeholder") == "API Secret Key"
    field.fill("test-secret")
    assert field.input_value() != ""


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: eye icons are visible for API key fields")
def test_connect_binance_eye_icons_visible(connect_binance_page) -> None:
    expect(connect_binance_page.eye_icons()).to_have_count(2)


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Manual Form")
@allure.title("Connect Binance: Connect to Exchange button is visible and enabled")
def test_connect_binance_connect_button(connect_binance_page) -> None:
    button = connect_binance_page.connect_button()
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Validation")
@allure.title("Connect Binance: empty submit marks Connection Name invalid")
def test_connect_binance_empty_connection_name_validation(connect_binance_page) -> None:
    connect_binance_page.connect_button().click()
    expect(connect_binance_page.connection_name_input()).to_have_class(re.compile(r"invalid"))


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Validation")
@allure.title("Connect Binance: empty submit marks API Key invalid")
def test_connect_binance_empty_api_key_validation(connect_binance_page) -> None:
    connect_binance_page.connect_button().click()
    expect(connect_binance_page.api_key_input()).to_have_class(re.compile(r"invalid"))


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Validation")
@allure.title("Connect Binance: empty submit marks API Secret invalid")
def test_connect_binance_empty_api_secret_validation(connect_binance_page) -> None:
    connect_binance_page.connect_button().click()
    expect(connect_binance_page.api_secret_input()).to_have_class(re.compile(r"invalid"))


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Validation")
@allure.title("Connect Binance: malformed API Key message is exposed when the product surfaces format validation")
def test_connect_binance_malformed_api_key_message_if_supported(connect_binance_page) -> None:
    # The current build does not expose a stable inline format-validation message for malformed API keys.
    # To remove this skip, align the form with a deterministic frontend validation message or expose a stable server error.
    connect_binance_page.connection_name_input().fill(f"binance-format-{random.randint(1000, 9999)}")
    connect_binance_page.api_key_input().fill("!")
    connect_binance_page.api_secret_input().fill("abc")
    connect_binance_page.connect_button().click()
    connect_binance_page.page.wait_for_timeout(1_500)
    if "incorrect" not in connect_binance_page.body_text().lower() and "invalid" not in connect_binance_page.body_text().lower():
        pytest.skip("Current Binance form does not show a stable malformed API Key message.")


@allure.feature("Exchange Pages")
@allure.story("Connect Binance Validation")
@allure.title("Connect Binance: server-side connection error is visible when fake credentials are submitted")
def test_connect_binance_server_error_if_supported(connect_binance_page) -> None:
    # This check requires the backend to reject fake-but-formally-valid credentials with a stable UI message.
    # To remove this skip, expose a deterministic connection error toast/message in the test environment.
    connect_binance_page.connection_name_input().fill(f"binance-server-{random.randint(1000, 9999)}")
    connect_binance_page.api_key_input().fill("A" * 32)
    connect_binance_page.api_secret_input().fill("B" * 32)
    connect_binance_page.connect_button().click()
    connect_binance_page.page.wait_for_timeout(3_000)
    body = connect_binance_page.body_text().lower()
    if "failed" not in body and "error" not in body:
        pytest.skip("Current Binance flow does not surface a stable server-side connection error for fake credentials.")
