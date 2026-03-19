import re

import allure
import pytest


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: deals table shows the expected columns")
def test_deals_table_headers_are_visible(logged_in_strategy_details_page) -> None:
    assert logged_in_strategy_details_page.deals_table_headers() == [
        "Strategy",
        "Pair",
        "Strategy",
        "Profit",
        "Volumes",
        "Status",
        "Update",
    ]


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: deals table contains at least one data row")
def test_deals_table_has_rows(logged_in_strategy_details_page) -> None:
    assert len(logged_in_strategy_details_page.deals_table_rows()) > 0


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: strategy direction is shown as Long or Short")
def test_deals_table_strategy_direction_is_allowed(logged_in_strategy_details_page) -> None:
    first_row = logged_in_strategy_details_page.first_deals_row()
    assert first_row[2] in {"Long", "Short"}, first_row


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: profit values are shown in USDT")
def test_deals_table_profit_value_format(logged_in_strategy_details_page) -> None:
    first_row = logged_in_strategy_details_page.first_deals_row()
    assert re.fullmatch(r"[+-]?\d+(?:\.\d+)?\s*USDT", first_row[3]), first_row


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: volume values are shown with the traded asset ticker")
def test_deals_table_volume_value_format(logged_in_strategy_details_page) -> None:
    first_row = logged_in_strategy_details_page.first_deals_row()
    assert re.fullmatch(r"[+-]?\d+(?:\.\d+)?\s+[A-Z0-9]+", first_row[4]), first_row


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: deal status is shown as ACTIVE or COMPLETED")
def test_deals_table_status_value_is_allowed(logged_in_strategy_details_page) -> None:
    first_row = logged_in_strategy_details_page.first_deals_row()
    assert first_row[5] in {"ACTIVE", "COMPLETED"}, first_row


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: update value shows a date and time")
def test_deals_table_update_value_format(logged_in_strategy_details_page) -> None:
    first_row = logged_in_strategy_details_page.first_deals_row()
    assert re.fullmatch(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{2}:\d{2}\s+[AP]M", first_row[6]), first_row


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: pagination is visible when more than one page of deals exists")
def test_deals_table_pagination_is_visible(logged_in_strategy_details_page) -> None:
    # This assertion only applies when the selected strategy has more than one page of deals.
    # To remove this skip, select/seed a strategy with enough history to produce pagination.
    if not logged_in_strategy_details_page.has_multiple_deal_pages():
        pytest.skip("Current strategy has only one deals page.")
    assert logged_in_strategy_details_page.pagination_root().is_visible()
    assert len(logged_in_strategy_details_page.pagination_page_numbers()) > 1


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: next-page pagination loads new rows within three seconds")
def test_deals_table_next_page_load_time(logged_in_strategy_details_page) -> None:
    # Pagination timing cannot be measured when there is only one deals page.
    # To remove this skip, use a strategy with multi-page deal history in the test environment.
    if not logged_in_strategy_details_page.has_multiple_deal_pages():
        pytest.skip("Current strategy has only one deals page.")
    duration_sec = logged_in_strategy_details_page.click_pagination_next()
    assert duration_sec <= 3.0, f"Expected pagination load <= 3.0 sec, got {duration_sec:.2f} sec"


@allure.feature("Marketplace Strategy Details")
@allure.story("Deals Table")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: previous and next pagination controls switch pages correctly")
def test_deals_table_prev_and_next_controls_work(logged_in_strategy_details_page) -> None:
    # Prev/next navigation is meaningful only for strategies with paginated deal history.
    # To remove this skip, target a seeded strategy that has at least two pages of deals.
    if not logged_in_strategy_details_page.has_multiple_deal_pages():
        pytest.skip("Current strategy has only one deals page.")
    assert logged_in_strategy_details_page.is_pagination_prev_disabled()
    logged_in_strategy_details_page.click_pagination_next()
    assert not logged_in_strategy_details_page.is_pagination_prev_disabled()
    logged_in_strategy_details_page.click_pagination_prev()
    assert logged_in_strategy_details_page.is_pagination_prev_disabled()
