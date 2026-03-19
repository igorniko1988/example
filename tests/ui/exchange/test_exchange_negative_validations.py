import random

import allure

from src.pages.auth_page import AuthPage
from src.pages.exchange_page import ExchangePage


@allure.feature("Exchange Accounts")
@allure.story("Binance Form Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Exchange Accounts: empty Binance form shows validation on all required fields")
def test_binance_connect_empty_submit_marks_all_fields_invalid(page, base_url, auth_email, auth_password) -> None:
    AuthPage(page, base_url).login(auth_email, auth_password)
    exchange = ExchangePage(page, base_url)
    exchange.open_binance_connect_form()
    exchange.fill_binance_connect_form()
    exchange.submit_connect_to_exchange()
    exchange.assert_invalid_inputs_count(3)
    exchange.assert_still_on_connect_binance_page()


@allure.feature("Exchange Accounts")
@allure.story("Binance Form Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Exchange Accounts: connection name only keeps API key and API secret required")
def test_binance_connect_requires_api_key_and_secret(page, base_url, auth_email, auth_password) -> None:
    AuthPage(page, base_url).login(auth_email, auth_password)
    exchange = ExchangePage(page, base_url)
    exchange.open_binance_connect_form()

    connection_name = f"binance-neg-{random.randint(1000, 9999)}"
    exchange.fill_binance_connect_form(connection_name=connection_name)
    exchange.submit_connect_to_exchange()
    exchange.assert_binance_field_invalid_state(
        connection_name_invalid=False,
        api_key_invalid=True,
        api_secret_invalid=True,
    )


@allure.feature("Exchange Accounts")
@allure.story("Binance Form Validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Exchange Accounts: missing API secret keeps only the API secret field invalid")
def test_binance_connect_requires_api_secret_when_name_and_api_key_are_filled(
    page, base_url, auth_email, auth_password
) -> None:
    AuthPage(page, base_url).login(auth_email, auth_password)
    exchange = ExchangePage(page, base_url)
    exchange.open_binance_connect_form()

    connection_name = f"binance-neg-{random.randint(1000, 9999)}"
    api_key = "invalid-key-123"
    exchange.fill_binance_connect_form(connection_name=connection_name, api_key=api_key)
    exchange.submit_connect_to_exchange()
    exchange.assert_binance_field_invalid_state(
        connection_name_invalid=False,
        api_key_invalid=False,
        api_secret_invalid=True,
    )
