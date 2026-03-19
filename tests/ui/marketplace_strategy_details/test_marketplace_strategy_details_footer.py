import allure
from playwright.sync_api import expect


@allure.feature("Marketplace Strategy Details")
@allure.story("Footer")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: support footer link opens the Telegram support bot")
def test_footer_support_link_destination(strategy_details_page) -> None:
    strategy_details_page.assert_redirect_destination(
        strategy_details_page.footer_support_link(),
        r"^https://t\.me/GT_App_CSbot/?",
        "Open footer support link",
    )


@allure.feature("Marketplace Strategy Details")
@allure.story("Footer")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: Terms footer link opens the Terms page")
def test_footer_terms_link_destination(strategy_details_page) -> None:
    strategy_details_page.assert_redirect_destination(
        strategy_details_page.footer_terms_link(),
        r"/terms/?$",
        "Open footer Terms link",
    )


@allure.feature("Marketplace Strategy Details")
@allure.story("Footer")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: Privacy Policy footer link opens the Privacy Policy page")
def test_footer_privacy_link_destination(strategy_details_page) -> None:
    strategy_details_page.assert_redirect_destination(
        strategy_details_page.footer_privacy_link(),
        r"/privacy-policy/?$",
        "Open footer Privacy Policy link",
    )


@allure.feature("Marketplace Strategy Details")
@allure.story("Footer")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace Strategy Details: footer copyright shows '© 2026 GT App'")
def test_footer_copyright_text(strategy_details_page) -> None:
    expect(strategy_details_page.footer_copyright()).to_be_visible()
