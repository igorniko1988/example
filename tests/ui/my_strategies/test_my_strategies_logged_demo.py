import re

import allure
import pytest
from playwright.sync_api import expect


@allure.feature("My Strategies")
@allure.story("Logged In Demo Trading")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in 'Demo Trading' section can be collapsed and expanded")
def test_logged_in_demo_section_can_toggle(logged_in_my_strategies_page) -> None:
    assert logged_in_my_strategies_page.section_expanded("Demo Trading")
    logged_in_my_strategies_page.toggle_section("Demo Trading")
    assert not logged_in_my_strategies_page.section_expanded("Demo Trading")
    logged_in_my_strategies_page.toggle_section("Demo Trading")
    assert logged_in_my_strategies_page.section_expanded("Demo Trading")


@allure.feature("My Strategies")
@allure.story("Logged In Demo Trading")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in 'Create Demo Strategy' is visible and clickable")
def test_logged_in_create_demo_strategy_is_clickable(logged_in_my_strategies_page) -> None:
    expect(logged_in_my_strategies_page.top_create_button("Create Demo Strategy")).to_be_visible()
    logged_in_my_strategies_page.click_top_create_button("Create Demo Strategy")
    expect(logged_in_my_strategies_page.page).to_have_url(re.compile(r"/dashboard/bot/create-demo"), timeout=30_000)


@allure.feature("My Strategies")
@allure.story("Logged In Demo Trading")
@allure.severity(allure.severity_level.MINOR)
@allure.title("My Strategies: logged-in demo cards are available for dedicated assertions when present")
def test_logged_in_demo_cards_presence(logged_in_my_strategies_page) -> None:
    # Current logged-in account has no demo cards in the Demo Trading section.
    # To remove this skip, run with an account that already has demo strategy cards
    # or add setup that seeds demo strategies before this suite.
    if not logged_in_my_strategies_page.demo_cards_payload():
        pytest.skip("No demo cards are visible for the current logged-in account.")
    assert logged_in_my_strategies_page.demo_cards_payload()
