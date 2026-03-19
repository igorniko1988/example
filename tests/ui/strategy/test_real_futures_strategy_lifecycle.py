import random
import re
import time

import allure
import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect

from src.pages.auth_page import AuthPage
from src.pages.exchange_page import ExchangePage
from src.pages.futures_strategy_page import FuturesStrategyPage


pytestmark = pytest.mark.skip(reason="Requires a dedicated real futures account.")
@allure.feature("Real Futures Trading")
@allure.story("Strategy Full Flow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Real Futures Trading: strategy can be created, started, closed and stopped")
def test_real_futures_strategy_lifecycle(
    page, context, base_url, auth_email, auth_password, binance_api_key, binance_api_secret
) -> None:
    exchange = ExchangePage(page, base_url)
    strategy = FuturesStrategyPage(page, base_url)

    exchange_name = f"binance-auto-{random.randint(10000, 99999)}"
    strategy_name = f"r{random.randint(10000, 99999)}"
    strategy_id: str | None = None
    exchange_created = False
    strategy_created = False
    strategy_deleted = False
    cleanup_errors: list[str] = []

    def ensure_exchange_accounts_empty(exchange_page: ExchangePage) -> None:
        remaining = exchange_page.ensure_no_connected_exchanges(attempts=5, max_delete_per_pass=20)
        assert not remaining, f"Connected exchanges must be empty before add-flow, got: {remaining}"
        exchange_page.wait_until_no_connected_exchanges(timeout_sec=10)

    def assert_exchange_visible(exchange_page: ExchangePage, connection_name: str) -> None:
        exchange_page.get_connected_exchange_names()
        connected_names = exchange_page.get_connected_exchange_names_from_current_page()
        assert connection_name in connected_names, (
            f"Expected exchange '{connection_name}' in connected exchanges list, got: {connected_names}"
        )

    def delete_exchange(exchange_page: ExchangePage, connection_name: str) -> None:
        exchange_page.get_connected_exchange_names()
        deleted = exchange_page.delete_exchange_account_if_exists(connection_name, navigate=False)
        if not deleted:
            try:
                exchange_page.wait_until_exchange_absent(connection_name, timeout_sec=15)
            except Exception:
                pass
            connected_names = exchange_page.get_connected_exchange_names_from_current_page()
            assert connection_name not in connected_names, (
                f"Exchange '{connection_name}' should already be absent if delete action did not run, got: {connected_names}"
            )
            return

        connected_names = exchange_page.get_connected_exchange_names_from_current_page()
        if connection_name in connected_names:
            remaining = exchange_page.ensure_no_connected_exchanges(attempts=5, max_delete_per_pass=20)
            assert connection_name not in remaining, (
                f"Exchange '{connection_name}' must be absent after deletion, got: {remaining}"
            )

    def delete_strategy(strategy_page: FuturesStrategyPage, target_name: str, target_id: str | None) -> None:
        for _ in range(3):
            if strategy_page.delete_futures_strategy_from_list_if_exists(target_name, target_id):
                return
            strategy_page.page.wait_for_timeout(2_000)
        raise AssertionError(f"Expected strategy '{target_name}' to be deleted from the strategies list.")

    try:
        AuthPage(page, base_url).login(auth_email, auth_password)

        with allure.step("Ensure no connected exchange accounts remain before the test"):
            ensure_exchange_accounts_empty(exchange)

        exchange.connect_binance_account(
            exchange_name,
            binance_api_key,
            binance_api_secret,
            verify_strategies_unlocked=False,
        )
        exchange_created = True

        with allure.step("Verify the connected Binance account is visible"):
            assert_exchange_visible(exchange, exchange_name)

        with allure.step("Refresh balances for the connected Binance account"):
            exchange.refresh_connected_exchange_balance(exchange_name)

        with allure.step("Open the Create Futures Strategy form"):
            strategy.open_futures_strategy_form()

        strategy.fill_required_futures_form_fields(
            strategy_name,
            exchange_name,
            trading_pair="XRP/USDT",
            start_order_amount="10",
            safety_order_amount="10",
        )

        with allure.step("Create and launch the real futures strategy"):
            _, save_to_created_sec = strategy.save_and_start_strategy()
            if save_to_created_sec is not None:
                allure.attach(
                    f"{save_to_created_sec:.2f} sec",
                    "save_start_to_strategy_created_duration",
                    allure.attachment_type.TEXT,
                )

        strategy_id = strategy.assert_strategy_details_page_opened()
        strategy_created = True

        with allure.step("Close the optional 'strategy launched' confirmation if it appears"):
            strategy.assert_strategy_popup_and_click_ok(
                [r"launched", r"strategy has been launched"],
                "launched",
                required=False,
            )

        start_deal_click_ts = strategy.click_start_deal()
        strategy.confirm_start_with_market_price()

        with allure.step("Close the optional 'new deal started' confirmation if it appears"):
            strategy.assert_strategy_popup_and_click_ok(
                [r"started\s+new\s+deal", r"start.*deal", r"new deal"],
                "start_deal",
                required=False,
            )

        with allure.step("Verify the trading log shows deal activity after Start Deal"):
            strategy.wait_for_trading_logs_patterns(
                [
                    r"start order.*placed",
                    r"start order.*executed",
                    r"placed a safety order",
                    r"take profit order",
                ],
                timeout_sec=120,
                refresh_every_sec=30,
                debug_name="start_deal_activity",
            )
            allure.attach(
                f"{time.monotonic() - start_deal_click_ts:.2f} sec",
                "start_deal_click_to_first_deal_activity_duration",
                allure.attachment_type.TEXT,
            )

        close_deal_click_ts = strategy.click_close_deal()

        strategy.assert_confirmation_dialog_and_click_yes(
            r"close deal",
            [r"close deal", r"are you sure", r"close.*position", r"deal"],
            "close_deal_confirm",
        )
        strategy.assert_strategy_popup_and_click_ok(
            [r"deal was canceled", r"close.*deal", r"deal.*closed", r"position.*closed"],
            "close_deal",
            required=False,
        )

        with allure.step("Verify the trading log shows the close position order was placed"):
            try:
                strategy.wait_for_front_event(
                    "close_position_order",
                    "opened",
                    timeout_sec=240,
                    refresh_every_sec=30,
                )
                allure.attach(
                    f"{time.monotonic() - close_deal_click_ts:.2f} sec",
                    "close_deal_click_to_close_order_opened_duration",
                    allure.attachment_type.TEXT,
                )
            except AssertionError as close_open_error:
                allure.attach(str(close_open_error), "close_position_order_open_refresh_retry", allure.attachment_type.TEXT)
                with allure.step("Recovery: refresh the page and re-check delayed close position order logs"):
                    page.reload(wait_until="domcontentloaded")
                    strategy.dismiss_ok_dialogs_if_present()
                strategy.wait_for_front_event(
                    "close_position_order",
                    "opened",
                    timeout_sec=180,
                    refresh_every_sec=30,
                )
                allure.attach(
                    f"{time.monotonic() - close_deal_click_ts:.2f} sec",
                    "close_deal_click_to_close_order_opened_duration_after_refresh",
                    allure.attachment_type.TEXT,
                )

        with allure.step("Verify the trading log shows the close position order was executed"):
            try:
                strategy.wait_for_front_event(
                    "close_position_order",
                    "closed",
                    timeout_sec=240,
                    refresh_every_sec=30,
                )
            except AssertionError as close_closed_error:
                allure.attach(str(close_closed_error), "close_position_order_closed_refresh_retry", allure.attachment_type.TEXT)
                with allure.step("Recovery: refresh the page and re-check delayed close position execution logs"):
                    page.reload(wait_until="domcontentloaded")
                    strategy.dismiss_ok_dialogs_if_present()
                strategy.wait_for_front_event(
                    "close_position_order",
                    "closed",
                    timeout_sec=180,
                    refresh_every_sec=30,
                )

        with allure.step("Verify the trading log shows the final deal completion message"):
            try:
                strategy.wait_for_trading_logs_patterns(
                    [
                        rf"{re.escape(strategy_name)}\.\s*Deal canceled\.\s*Your profit\s*[-+]?\d+(?:\.\d+)?\s*USDT\.\s*[-+]?\d+(?:\.\d+)?%\s*of total deal volume",
                        r"deal canceled",
                    ],
                    timeout_sec=240,
                    refresh_every_sec=30,
                    debug_name="deal_canceled_profit",
                )
            except AssertionError as deal_canceled_error:
                allure.attach(str(deal_canceled_error), "deal_canceled_refresh_retry", allure.attachment_type.TEXT)
                with allure.step("Recovery: refresh the page and re-check delayed final deal logs"):
                    page.reload(wait_until="domcontentloaded")
                    strategy.dismiss_ok_dialogs_if_present()
                strategy.wait_for_trading_logs_patterns(
                    [
                        rf"{re.escape(strategy_name)}\.\s*Deal canceled\.\s*Your profit\s*[-+]?\d+(?:\.\d+)?\s*USDT\.\s*[-+]?\d+(?:\.\d+)?%\s*of total deal volume",
                        r"deal canceled",
                    ],
                    timeout_sec=180,
                    refresh_every_sec=30,
                    debug_name="deal_canceled_profit_after_refresh",
                )

        strategy.click_stop_strategy()

        strategy.assert_confirmation_dialog_and_click_yes_if_visible(
            r"stop",
            [r"stop", r"are you sure", r"strategy"],
            "stop_strategy_confirm",
        )
        strategy.assert_front_notification([r"stopped", r"strategy has been stopped"], "stopped")
        strategy.assert_strategy_popup_and_click_ok([r"stopped", r"strategy has been stopped"], "stopped", required=False)
        strategy.dismiss_ok_dialogs_if_present()

        with allure.step("Open My Strategies after stopping the strategy"):
            page.goto(f"{base_url}/dashboard/bot/list", wait_until="domcontentloaded")
            expect(page).to_have_url(re.compile(r"/dashboard/bot/list"), timeout=30_000)
            strategy.dismiss_ok_dialogs_if_present()

        with allure.step("Delete the futures strategy from My Strategies"):
            delete_strategy(strategy, strategy_name, strategy_id)
            strategy_deleted = True

        with allure.step("Open Exchange Accounts and wait for a stable account state"):
            page.goto(f"{base_url}/dashboard/exchange", wait_until="domcontentloaded")
            expect(page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)
            exchange.get_connected_exchange_names_from_current_page()

        with allure.step("Delete the connected Binance account"):
            delete_exchange(exchange, exchange_name)
            exchange_created = False
    finally:
        cleanup_page = page
        opened_cleanup_page = False
        if cleanup_page.is_closed():
            try:
                cleanup_page = context.new_page()
                cleanup_page.set_default_timeout(20_000)
                opened_cleanup_page = True
                AuthPage(cleanup_page, base_url).login(auth_email, auth_password)
            except Exception as cleanup_error:
                allure.attach(str(cleanup_error), "cleanup_new_page_or_login_error", allure.attachment_type.TEXT)
                cleanup_errors.append(f"cleanup page/login failed: {cleanup_error}")

        cleanup_exchange = ExchangePage(cleanup_page, base_url)
        cleanup_strategy = FuturesStrategyPage(cleanup_page, base_url)

        with allure.step("Cleanup fallback: remove the strategy if it still exists"):
            try:
                if strategy_created and not strategy_deleted:
                    delete_strategy(cleanup_strategy, strategy_name, strategy_id)
                    strategy_deleted = True
            except Exception as cleanup_error:
                allure.attach(str(cleanup_error), "cleanup_strategy_delete_error", allure.attachment_type.TEXT)
                cleanup_errors.append(f"strategy cleanup failed: {cleanup_error}")

        with allure.step("Cleanup fallback: remove the exchange account if it still exists"):
            try:
                if exchange_created:
                    delete_exchange(cleanup_exchange, exchange_name)
                    exchange_created = False
            except Exception as cleanup_error:
                allure.attach(str(cleanup_error), "cleanup_exchange_delete_error", allure.attachment_type.TEXT)
                cleanup_errors.append(f"target exchange cleanup failed: {cleanup_error}")

        with allure.step("Cleanup fallback: remove any remaining connected exchange accounts"):
            try:
                remaining_after_purge = cleanup_exchange.ensure_no_connected_exchanges(attempts=5, max_delete_per_pass=20)
                cleanup_exchange.wait_until_no_connected_exchanges(timeout_sec=10)
                if remaining_after_purge:
                    allure.attach(
                        "\n".join(remaining_after_purge),
                        "cleanup_remaining_exchange_connections_after_purge",
                        allure.attachment_type.TEXT,
                    )
                    raise AssertionError(
                        f"Connected exchanges remain after final purge: {remaining_after_purge}"
                    )
            except Exception as cleanup_error:
                allure.attach(str(cleanup_error), "cleanup_exchange_purge_error", allure.attachment_type.TEXT)
                cleanup_errors.append(f"exchange purge cleanup failed: {cleanup_error}")

        try:
            if opened_cleanup_page and not cleanup_page.is_closed():
                cleanup_page.close()
        except PlaywrightError:
            pass

        if cleanup_errors:
            raise AssertionError("Cleanup failed: " + " | ".join(cleanup_errors))
