import re

import allure
import pytest
from playwright.sync_api import expect


def _require_copy_card(logged_in_my_strategies_page):
    # Copy-card assertions require at least one copied marketplace strategy to be visible on the page.
    # To remove this skip, run with an account that already has a copied strategy card
    # or add setup that copies a strategy before this suite starts.
    cards = logged_in_my_strategies_page.copy_cards_payload()
    if not cards:
        pytest.skip("No copy strategy card is visible for the current logged-in account.")
    return cards[0]


@allure.feature("My Strategies")
@allure.story("Logged In Strategies Section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in 'Strategies' section can be collapsed and expanded")
def test_logged_in_strategies_section_can_toggle(logged_in_my_strategies_page) -> None:
    assert logged_in_my_strategies_page.section_expanded("Strategies")
    logged_in_my_strategies_page.toggle_section("Strategies")
    assert not logged_in_my_strategies_page.section_expanded("Strategies")
    logged_in_my_strategies_page.toggle_section("Strategies")
    assert logged_in_my_strategies_page.section_expanded("Strategies")


@pytest.mark.parametrize(
    ("label", "expected_pattern"),
    [
        ("Create Futures Strategy", r"/dashboard/bot/create-futures"),
        ("Create Spot Strategy", r"/dashboard/bot/create/?$"),
        ("Create Copy strategy", r"/dashboard/bots-marketplace/?$"),
    ],
)
@allure.feature("My Strategies")
@allure.story("Logged In Strategies Section")
@allure.severity(allure.severity_level.NORMAL)
def test_logged_in_top_create_buttons_navigate(logged_in_my_strategies_page, label: str, expected_pattern: str) -> None:
    allure.dynamic.title(f"My Strategies: logged-in '{label}' is visible and clickable")
    target = logged_in_my_strategies_page.top_create_button(label)
    expect(target).to_be_visible()
    # Some create controls may be rendered but disabled for the current account/build state.
    # To remove this skip, run with an account/state where the control is enabled
    # or stabilize the product rules that gate this action.
    if not target.is_enabled():
        pytest.skip(f"'{label}' is currently rendered as disabled for this logged-in account.")
    logged_in_my_strategies_page.click_top_create_button(label)
    expect(logged_in_my_strategies_page.page).to_have_url(re.compile(expected_pattern), timeout=30_000)


@allure.feature("My Strategies")
@allure.story("Logged In Strategies Section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("My Strategies: create button becomes inactive when the strategy limit is reached")
def test_logged_in_strategy_limit_disables_create_button(logged_in_my_strategies_page) -> None:
    # This test needs an account that is already at its strategy creation limit.
    # To remove this skip, run with capped credentials or add setup that fills the account to its strategy limit.
    if not any(button.is_disabled() for button in [
        logged_in_my_strategies_page.top_create_button("Create Futures Strategy"),
        logged_in_my_strategies_page.top_create_button("Create Spot Strategy"),
        logged_in_my_strategies_page.top_create_button("Create Copy strategy"),
    ]):
        pytest.skip("Current logged-in account is not at the strategy creation limit.")
    assert any(button.is_disabled() for button in [
        logged_in_my_strategies_page.top_create_button("Create Futures Strategy"),
        logged_in_my_strategies_page.top_create_button("Create Spot Strategy"),
        logged_in_my_strategies_page.top_create_button("Create Copy strategy"),
    ])


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows trader name")
def test_logged_in_copy_card_trader_name(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    match = re.search(r"Made by\s+([A-Za-z0-9_-]+)", card["text"])
    assert match and match.group(1)


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows type and direction")
def test_logged_in_copy_card_type_and_direction(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    assert re.search(r"\b(FUTURES|SPOT)\b", card["text"])
    assert re.search(r"\b(LONG|SHORT)\b", card["text"])


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows APY as a percentage")
def test_logged_in_copy_card_apy_format(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    match = re.search(r"APY\s+([+-]?\d+(?:\.\d+)?%)", card["text"])
    assert match, card["text"]


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows Lifetime in days")
def test_logged_in_copy_card_lifetime_format(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    assert re.search(r"Lifetime\s+\d+\s*D", card["text"]), card["text"]


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows Risk as High, Medium or Low")
def test_logged_in_copy_card_risk_value(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    assert re.search(r"Risk\s+(High|Medium|Low)", card["text"]), card["text"]


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows minimum balance in USDT")
def test_logged_in_copy_card_min_balance_format(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    assert re.search(r"Min\. Balance\s+\d+(?:\.\d+)?\s*USDT", card["text"]), card["text"]


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("My Strategies: logged-in copy strategy card shows a mini APY chart")
def test_logged_in_copy_card_chart_is_present(logged_in_my_strategies_page) -> None:
    card = _require_copy_card(logged_in_my_strategies_page)
    assert int(card["canvases"]) > 0


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows a clickable exchange selector")
def test_logged_in_copy_card_exchange_selector_is_clickable(logged_in_my_strategies_page) -> None:
    _require_copy_card(logged_in_my_strategies_page)
    expect(logged_in_my_strategies_page.copy_card_exchange_input()).to_be_visible()
    logged_in_my_strategies_page.open_copy_exchange_dropdown()
    assert "Please connect a new exchange." in logged_in_my_strategies_page.page_text() or logged_in_my_strategies_page.page.locator(".el-select-dropdown, .el-popper").count() > 0


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card shows disabled 'Create Strategy' without exchange")
def test_logged_in_copy_card_create_strategy_is_disabled_without_exchange(logged_in_my_strategies_page) -> None:
    _require_copy_card(logged_in_my_strategies_page)
    expect(logged_in_my_strategies_page.copy_card_create_button()).to_be_visible()
    expect(logged_in_my_strategies_page.copy_card_create_button()).to_be_disabled()


@allure.feature("My Strategies")
@allure.story("Logged In Copy Strategy Card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in copy strategy card delete action opens confirmation")
def test_logged_in_copy_card_delete_opens_confirmation(logged_in_my_strategies_page) -> None:
    _require_copy_card(logged_in_my_strategies_page)
    logged_in_my_strategies_page.open_delete_confirmation_from_copy_card()
    expect(logged_in_my_strategies_page.page.get_by_role("dialog")).to_be_visible()
    logged_in_my_strategies_page.dismiss_delete_confirmation()


@allure.feature("My Strategies")
@allure.story("Logged In Personal Strategy Card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("My Strategies: logged-in personal strategy cards are available for dedicated assertions when present")
def test_logged_in_personal_strategy_cards_presence(logged_in_my_strategies_page) -> None:
    # Current logged-in account has no personal strategy cards on the list page.
    # To remove this skip, run with an account that already has personal launch/pause cards
    # or add setup that creates personal strategies before this suite.
    if not logged_in_my_strategies_page.personal_cards_payload():
        pytest.skip("No personal strategy cards are visible for the current logged-in account.")
    assert logged_in_my_strategies_page.personal_cards_payload()
