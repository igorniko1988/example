import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Profile")
@allure.story("Page Load")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Profile: page loads without errors and records the actual load time")
def test_profile_page_loads_within_three_seconds(logged_in_profile_page) -> None:
    logged_in_profile_page.measure_warm_load()
    logged_in_profile_page.assert_load_time_not_more_than(3.0)


@allure.feature("Profile")
@allure.story("Page Shell")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'My Profile' heading is visible")
@pytest.mark.smoke
def test_profile_heading_is_visible(logged_in_profile_page) -> None:
    expect(logged_in_profile_page.heading("My Profile", level=1)).to_be_visible()
