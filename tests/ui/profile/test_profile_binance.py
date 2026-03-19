import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Profile")
@allure.story("Binance Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Binance Account' heading is visible")
def test_binance_account_heading_is_visible(logged_in_profile_page) -> None:
    expect(logged_in_profile_page.heading("Binance Account", level=5)).to_be_visible()


@allure.feature("Profile")
@allure.story("Binance Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Link Binance Account' button is visible and enabled")
def test_binance_link_button_is_visible_and_clickable(logged_in_profile_page) -> None:
    button = logged_in_profile_page.binance_link_button()
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Profile")
@allure.story("Binance Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: clicking 'Link Binance Account' opens Binance OAuth in the same tab")
def test_binance_link_opens_oauth(logged_in_profile_page) -> None:
    logged_in_profile_page.open_binance_oauth()
    logged_in_profile_page.assert_binance_oauth_opened()


@allure.feature("Profile")
@allure.story("Binance Account")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Profile: Binance connection info text is shown when an account is already linked")
def test_binance_linked_info_text_is_visible(logged_in_profile_page) -> None:
    # This assertion only applies when the current account already has a linked Binance account.
    # To remove this skip, run with a pre-linked Binance test account
    # or add setup that creates the linked state before opening Profile.
    if "This account is connected to a Binance account via" not in logged_in_profile_page.page.locator("body").inner_text():
        pytest.skip("No pre-linked Binance account is visible for this session.")
    logged_in_profile_page.assert_binance_info_text_visible()


@allure.feature("Profile")
@allure.story("Binance Account")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Profile: Binance subtitle is visible")
def test_binance_subtitle_is_visible(logged_in_profile_page) -> None:
    logged_in_profile_page.assert_binance_subtitle_visible()
