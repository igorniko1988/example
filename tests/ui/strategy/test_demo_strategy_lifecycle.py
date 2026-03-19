import time

import allure

from src.pages.auth_page import AuthPage
from src.pages.demo_strategy_page import DemoStrategyPage
from src.utils.allure_helpers import attach_expected_actual


@allure.feature("Demo Trading")
@allure.story("Strategy Full Flow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Demo Trading: strategy can be created, started, closed, stopped and deleted")
def test_demo_strategy_lifecycle(base_url, auth_email, auth_password, page) -> None:
    demo = DemoStrategyPage(page, base_url)
    strategy_name = demo.generate_strategy_name()
    strategy_deleted = False

    try:
        AuthPage(page, base_url).login(auth_email, auth_password)
        demo.open_demo_strategy_form()
        demo.fill_required_demo_form_fields(strategy_name)

        with allure.step("Create and launch the demo strategy"):
            _, save_to_created_sec = demo.save_and_start_strategy()
            if save_to_created_sec is not None:
                allure.attach(
                    f"{save_to_created_sec:.2f} sec",
                    "save_start_to_strategy_created_duration",
                    allure.attachment_type.TEXT,
                )

        with allure.step("Verify the trading log shows strategy activation"):
            demo.wait_for_front_event("strategy", "activated", timeout_sec=240)

        demo.assert_strategy_details_page_opened()

        demo.assert_front_notification([r"launched", r"strategy has been launched"], "launched")
        demo.assert_strategy_popup_and_click_ok([r"launched", r"strategy has been launched"], "launched")

        start_deal_click_ts = demo.click_start_deal()

        demo.assert_strategy_popup_and_click_ok([r"started\s+new\s+deal", r"start.*deal", r"new deal"], "start_deal")
        with allure.step("Verify the trading log shows the start order was placed"):
            demo.wait_for_front_event(
                "start_order",
                "opened",
                timeout_sec=120,
                fallback_patterns=[
                    r"start order was executed",
                    r"start order.*executed",
                    r"the start order has been executed",
                    r"start order has been executed",
                ],
            )
            allure.attach(
                f"{time.monotonic() - start_deal_click_ts:.2f} sec",
                "start_deal_click_to_start_order_opened_duration",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify the trading log shows the start order was executed"):
            demo.wait_for_front_event("start_order", "closed", timeout_sec=120)

        close_deal_click_ts = demo.click_close_deal()

        demo.assert_confirmation_dialog_and_click_yes(
            r"close deal",
            [r"close deal", r"are you sure", r"close.*position", r"deal"],
            "close_deal_confirm",
        )
        demo.assert_strategy_popup_and_click_ok(
            [r"deal was canceled", r"close.*deal", r"deal.*closed", r"position.*closed"],
            "close_deal",
        )

        with allure.step("Verify the trading log shows the close position order was placed"):
            demo.wait_for_front_event(
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

        with allure.step("Verify the trading log shows the close position order was executed"):
            demo.wait_for_front_event(
                "close_position_order",
                "closed",
                timeout_sec=240,
                refresh_every_sec=30,
            )

        with allure.step("Verify the trading log shows the deal completed with profit data"):
            demo.wait_for_front_event(
                "deal",
                "completed",
                timeout_sec=420,
                refresh_every_sec=30,
            )

        demo.assert_strategy_popup_and_click_ok(
            [
                r"deal.*completed",
                r"deal was completed",
                r"total profit",
                r"daily profit",
                r"deal closing order has been executed",
            ],
            "deal_completed",
            required=False,
        )

        demo.click_stop_strategy()

        demo.assert_confirmation_dialog_and_click_yes_if_visible(
            r"stop",
            [r"stop", r"are you sure", r"strategy"],
            "stop_strategy_confirm",
        )
        demo.assert_front_notification([r"stopped", r"strategy has been stopped"], "stopped")
        demo.assert_strategy_popup_and_click_ok([r"stopped", r"strategy has been stopped"], "stopped", required=False)

        with allure.step("Delete the demo strategy from the list"):
            demo.dismiss_ok_dialogs_if_present()
            deleted_now = demo.delete_demo_strategy_from_list_if_exists(strategy_name)
            assert deleted_now, "Strategy should be deleted in main flow."
            strategy_deleted = True
    finally:
        with allure.step("Cleanup: remove the demo strategy if it still exists"):
            try:
                deleted = False if strategy_deleted else demo.delete_demo_strategy_from_list_if_exists(strategy_name)
                attach_expected_actual(
                    "Strategy should be absent after cleanup",
                    f"cleanup deleted strategy: {deleted}",
                )
            except Exception as cleanup_error:
                allure.attach(str(cleanup_error), "cleanup_error", allure.attachment_type.TEXT)
                allure.attach(
                    "Cleanup failed after retries. Test flow result is kept, cleanup issue is logged for follow-up.",
                    "cleanup_non_blocking_warning",
                    allure.attachment_type.TEXT,
                )
        with allure.step("Cleanup: remove leftover autogenerated demo strategies"):
            try:
                purged = demo.purge_test_demo_strategies(name_pattern=r"^d\d{5}$", max_delete=40)
                attach_expected_actual(
                    "No leftover test demo strategies should remain",
                    f"purged test strategies count: {purged}",
                )
            except Exception as purge_error:
                allure.attach(str(purge_error), "cleanup_purge_error", allure.attachment_type.TEXT)
