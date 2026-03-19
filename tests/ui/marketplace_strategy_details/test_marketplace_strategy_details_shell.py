import re

import allure


@allure.feature("Marketplace Strategy Details")
@allure.story("Page Shell")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: page loads without errors and records the actual load time")
def test_strategy_details_page_loads_within_three_seconds(strategy_details_page) -> None:
    duration_sec = strategy_details_page.measure_warm_load()
    assert duration_sec <= 3.0, f"Expected warm load <= 3.0 sec, got {duration_sec:.2f} sec"


@allure.feature("Marketplace Strategy Details")
@allure.story("Navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace Strategy Details: 'List of Strategies' returns the user to the Marketplace page")
def test_list_of_strategies_button_returns_to_marketplace(strategy_details_page) -> None:
    strategy_details_page.assert_redirect_destination(
        strategy_details_page.list_of_strategies_button(),
        r"/dashboard/bots-marketplace/?$",
        "Click 'List of Strategies'",
    )


@allure.feature("Marketplace Strategy Details")
@allure.story("Page Shell")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace Strategy Details: page heading shows the strategy name and trader name")
def test_strategy_details_heading_format(strategy_details_page) -> None:
    heading = strategy_details_page.heading_text()
    assert re.fullmatch(r".+ strategy by Top Trader .+", heading), heading
