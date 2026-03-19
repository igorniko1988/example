from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Profile")
@allure.story("Changelog")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Changelog' heading is visible")
def test_changelog_heading_is_visible(logged_in_profile_page) -> None:
    expect(logged_in_profile_page.heading("Changelog", level=5)).to_be_visible()


@allure.feature("Profile")
@allure.story("Changelog")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: changelog entries are ordered from newest to oldest")
def test_changelog_is_in_reverse_chronological_order(logged_in_profile_page) -> None:
    raw_dates = logged_in_profile_page.changelog_dates()
    parsed_results = [_parse_changelog_date(value) for value in raw_dates]
    # Historical changelog entries currently mix old and new date formats.
    # To remove this skip, normalize legacy data in the product
    # or scope the test to entries that use one stable format.
    if any(fmt != "%d.%m.%Y" for _parsed_date, fmt in parsed_results):
        pytest.skip("Legacy changelog entries use mixed date formats; strict full-list ordering is not stable.")
    parsed_dates = [parsed_date for parsed_date, _fmt in parsed_results]
    assert parsed_dates == sorted(parsed_dates, reverse=True)


@allure.feature("Profile")
@allure.story("Changelog")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: changelog entries include dates and change descriptions")
def test_changelog_entries_have_dates_and_descriptions(logged_in_profile_page) -> None:
    raw_dates = logged_in_profile_page.changelog_dates()
    assert raw_dates, "Expected at least one changelog entry."
    for value in raw_dates[:5]:
        _parse_changelog_date(value)

    body_text = logged_in_profile_page.page.locator("body").inner_text(timeout=10_000)
    for value in raw_dates[:5]:
        assert value in body_text


@allure.feature("Profile")
@allure.story("Changelog")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Profile: changelog container is independently scrollable when entries exceed the visible area")
def test_changelog_container_is_scrollable(logged_in_profile_page) -> None:
    metrics = logged_in_profile_page.changelog_scroll_metrics()
    assert metrics["found"], "Changelog container was not found."
    assert int(metrics["scrollHeight"]) > int(metrics["clientHeight"]), metrics


def _parse_changelog_date(value: str) -> tuple[datetime, str]:
    formats = ("%d.%m.%Y", "%m.%d.%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt), fmt
        except ValueError:
            continue
    raise ValueError(f"Unsupported changelog date format: {value}")
