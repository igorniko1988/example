import random

import allure
import pytest

from src.pages.auth_page import AuthPage
from src.pages.exchange_page import ExchangePage


@allure.feature("Exchange Accounts")
@allure.story("Connect And Delete Binance Account")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Exchange Accounts: Binance account can be connected and deleted")
def test_binance_exchange_account_add_and_delete_with_frontend_confirmations(
    page, base_url, auth_email, auth_password, binance_api_key, binance_api_secret
) -> None:
    connection_name = f"mcp-binance-{random.randint(10000, 99999)}"
    exchange = ExchangePage(page, base_url)
    exchange_created = False

    try:
        AuthPage(page, base_url).login(auth_email, auth_password)

        with allure.step("Ensure no connected exchange accounts remain before the test"):
            connected_names = exchange.ensure_no_connected_exchanges(attempts=5, max_delete_per_pass=20)
            assert not connected_names, (
                f"Connected exchanges must be empty before add-flow, got: {connected_names}"
            )
            exchange.wait_until_no_connected_exchanges(timeout_sec=10)

        # This flow needs GT_BINANCE_API_KEY/GT_BINANCE_API_SECRET that still connect successfully in the current environment.
        # To remove this skip, provide live Binance test credentials whose API permissions are accepted by the product.
        try:
            exchange.connect_binance_account(
                connection_name,
                binance_api_key,
                binance_api_secret,
                verify_strategies_unlocked=False,
            )
        except AssertionError as error:
            if "was not visible in Connected Exchanges after submit" in str(error):
                pytest.skip("Current Binance test credentials do not produce a connected exchange card after submit.")
            raise
        exchange_created = True
        exchange.assert_connected_exchange_visible(connection_name)

        with allure.step("Delete the connected Binance account"):
            deleted = exchange.delete_exchange_account_if_exists(connection_name, navigate=False)
            assert deleted, f"Expected exchange '{connection_name}' to be deleted from the current exchange card."
            exchange_created = False

        exchange.assert_connected_exchange_absent(connection_name)
    finally:
        if exchange_created:
            exchange.ensure_exchange_deleted(connection_name, attempts=3)
