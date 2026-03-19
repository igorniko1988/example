import re

import allure


@allure.feature("Marketplace")
@allure.story("Page Shell And Footer")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Marketplace: page shell, banners, title and footer are displayed")
def test_marketplace_shell_banners_and_footer(logged_in_marketplace_page) -> None:
    logged_in_marketplace_page.assert_loaded_without_errors()
    logged_in_marketplace_page.assert_page_title()
    logged_in_marketplace_page.assert_limited_time_offer_timer_format_when_present()
    logged_in_marketplace_page.assert_backtest_banner_copy()
    logged_in_marketplace_page.assert_footer_shell()


@allure.feature("Marketplace")
@allure.story("External Navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace: Backtest CTA and footer links open the correct destinations")
def test_marketplace_backtest_cta_and_footer_links(marketplace_page) -> None:
    checks = [
        ("Open Backtest CTA destination", marketplace_page.backtest_cta(), r"^https://backtest\.gt-protocol\.io/?"),
        ("Open support footer link destination", marketplace_page.footer_support_link(), r"^https://t\.me/GT_App_CSbot"),
        ("Open Terms footer link destination", marketplace_page.footer_terms_link(), r"/terms$"),
        ("Open Privacy Policy footer link destination", marketplace_page.footer_privacy_link(), r"/privacy-policy$"),
    ]

    for step_name, target, expected_url_pattern in checks:
        marketplace_page.assert_redirect_destination(target, expected_url_pattern, step_name)
