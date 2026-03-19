import allure
from playwright.sync_api import expect


@allure.feature("My Strategies")
@allure.story("Logged In Page Shell")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("My Strategies: logged-in page loads without errors and records the actual load time")
def test_logged_in_page_loads_within_three_seconds(logged_in_my_strategies_page) -> None:
    duration_sec = logged_in_my_strategies_page.measure_warm_load()
    assert duration_sec <= 3.0, f"Expected warm load <= 3.0 sec, got {duration_sec:.2f} sec"


@allure.feature("My Strategies")
@allure.story("Logged In Page Shell")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("My Strategies: logged-in page shows the 'My Strategies' heading")
def test_logged_in_heading_is_visible(logged_in_my_strategies_page) -> None:
    expect(logged_in_my_strategies_page.heading()).to_be_visible()
