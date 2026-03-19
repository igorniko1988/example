import re

import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: trader avatar is loaded without image errors")
def test_trader_avatar_is_loaded(strategy_details_page) -> None:
    expect(strategy_details_page.trader_avatar()).to_be_visible()
    assert strategy_details_page.is_image_loaded(strategy_details_page.trader_avatar())


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: trader name is visible and non-empty")
def test_trader_name_is_visible(strategy_details_page) -> None:
    trader_name = strategy_details_page.trader_name()
    assert trader_name, "Expected a non-empty trader name on the details page."


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: APY is shown as a percentage value")
def test_apy_value_format(strategy_details_page) -> None:
    apy_value = strategy_details_page.apy_value()
    assert re.fullmatch(r"[+-]?\d+(?:\.\d+)?%", apy_value), apy_value


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: Lifetime is shown as a day count")
def test_lifetime_value_format(strategy_details_page) -> None:
    lifetime_value = strategy_details_page.lifetime_value()
    assert re.fullmatch(r"\d+\s*D", lifetime_value), lifetime_value


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: Risk is shown as High, Medium or Low")
def test_risk_value_is_allowed(strategy_details_page) -> None:
    assert strategy_details_page.risk_value() in {"High", "Medium", "Low"}


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: minimum balance is shown in USDT")
def test_min_balance_value_format(strategy_details_page) -> None:
    min_balance_value = strategy_details_page.min_balance_value()
    assert re.fullmatch(r"[+-]?\d+(?:\.\d+)?\s*USDT", min_balance_value), min_balance_value


@allure.feature("Marketplace Strategy Details")
@allure.story("Summary")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: total profit is shown in USDT")
def test_total_profit_value_format(strategy_details_page) -> None:
    total_profit_value = strategy_details_page.total_profit_value()
    assert re.fullmatch(r"[+-]?\d+(?:\.\d+)?\s*USDT", total_profit_value), total_profit_value


@allure.feature("Marketplace Strategy Details")
@allure.story("Copy Strategy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: COPY is visible and enabled")
def test_copy_button_is_visible_and_enabled(strategy_details_page) -> None:
    expect(strategy_details_page.copy_button()).to_be_visible()
    expect(strategy_details_page.copy_button()).to_be_enabled()


@allure.feature("Marketplace Strategy Details")
@allure.story("Copy Strategy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: unauthenticated COPY redirects to registration")
def test_copy_redirects_unauthenticated_user_to_register(strategy_details_page) -> None:
    strategy_details_page.copy_button().click()
    expect(strategy_details_page.page).to_have_url(re.compile(r"/auth\?tab=register"), timeout=30_000)


@allure.feature("Marketplace Strategy Details")
@allure.story("Copy Strategy")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: authenticated COPY shows the membership limit message when the account cannot copy more strategies")
def test_authenticated_copy_membership_limit_feedback(logged_in_strategy_details_page) -> None:
    outcome = logged_in_strategy_details_page.click_copy_as_authenticated_user()
    # This check needs an account already capped by its current subscription plan.
    # To remove this skip, run with credentials that cannot copy more strategies
    # or add a dedicated fixture that prepares that account state before the test.
    if outcome == "copied":
        pytest.skip("Current authenticated account can still copy the strategy, so membership-limit feedback is not applicable.")
    assert outcome == "membership_limit", f"Expected membership-limit feedback, got {outcome!r}"
