import re

import allure
import pytest
from playwright.sync_api import expect


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: page loads within three seconds")
def test_exchange_overview_loads_within_three_seconds(exchange_overview_page) -> None:
    duration_sec = exchange_overview_page.measure_warm_load()
    assert duration_sec <= 3.0, f"Expected warm load <= 3.0 sec, got {duration_sec:.2f} sec"


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: heading is visible")
@pytest.mark.smoke
def test_exchange_overview_heading(exchange_overview_page) -> None:
    expect(exchange_overview_page.heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: safety banner is visible")
def test_exchange_overview_banner(exchange_overview_page) -> None:
    expect(exchange_overview_page.banner()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Binance card shows the logo")
def test_exchange_overview_binance_logo(exchange_overview_page) -> None:
    expect(exchange_overview_page.binance_logo()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Connect Binance button is visible and enabled")
def test_exchange_overview_connect_binance_button(exchange_overview_page) -> None:
    button = exchange_overview_page.connect_binance_button()
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Connect Binance opens the Binance connection page")
def test_exchange_overview_open_binance(exchange_overview_page) -> None:
    exchange_overview_page.open_binance_form()
    assert exchange_overview_page.page.url.endswith("/dashboard/connect-binance")


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Register now opens Binance registration in a new tab")
def test_exchange_overview_register_now_link(exchange_overview_page) -> None:
    popup = exchange_overview_page.open_register_popup()
    try:
        assert popup.url.startswith("https://accounts.binance.com/en/register")
    finally:
        popup.close()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Hyperliquid card shows the logo")
def test_exchange_overview_hyperliquid_logo(exchange_overview_page) -> None:
    expect(exchange_overview_page.hyperliquid_logo()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Connect Hyperliquid button is visible and enabled")
def test_exchange_overview_connect_hyperliquid_button(exchange_overview_page) -> None:
    button = exchange_overview_page.connect_hyperliquid_button()
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Connect Hyperliquid opens the Hyperliquid connection page")
def test_exchange_overview_open_hyperliquid(exchange_overview_page) -> None:
    exchange_overview_page.open_hyperliquid_form()
    assert exchange_overview_page.page.url.endswith("/dashboard/connect-hyperliquid")


@allure.feature("Exchange Pages")
@allure.story("Exchange Overview")
@allure.title("Exchange overview: Hyperliquid signup link opens in a new tab")
def test_exchange_overview_hyperliquid_signup_link(exchange_overview_page) -> None:
    popup = exchange_overview_page.open_hyperliquid_signup_popup()
    try:
        assert popup.url.startswith("https://app.hyperliquid.xyz/join/GTPROTOCOL")
    finally:
        popup.close()


@allure.feature("Exchange Pages")
@allure.story("Connected Exchanges")
@allure.title("Exchange overview: connected exchanges section is visible when at least one exchange is linked")
def test_connected_exchanges_section_if_present(exchange_overview_page) -> None:
    # This assertion needs an account that already has at least one linked exchange.
    # To remove this skip, run with a seeded account that contains a connected Binance or Hyperliquid account.
    if not exchange_overview_page.has_connected_exchanges():
        pytest.skip("Current account does not expose a Connected Exchanges section.")
    expect(exchange_overview_page.connected_exchanges_heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connected Exchanges")
@allure.title("Exchange overview: connected exchange cards show account name and exchange type")
def test_connected_exchange_rows_format_if_present(exchange_overview_page) -> None:
    # This check depends on linked exchange cards being present in the current account state.
    # To remove this skip, prepare an account with at least one connected exchange before running the suite.
    if not exchange_overview_page.has_connected_exchanges():
        pytest.skip("Current account has no connected exchange cards to validate.")
    rows = exchange_overview_page.connected_exchange_rows()
    assert rows, "Expected at least one connected exchange row."
    for row in rows:
        assert re.search(r".+\s*/\s*(Binance|Hyperliquid)$", row, re.I), row
