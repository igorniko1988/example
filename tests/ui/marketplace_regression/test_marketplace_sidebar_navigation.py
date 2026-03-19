import allure
import pytest


@allure.feature("Marketplace")
@allure.story("Sidebar Links")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    ("label", "expected_url_pattern"),
    [
        ("TOP Traders", r"/dashboard/bots-marketplace/?$"),
        ("My Strategies", r"/dashboard/bot/list"),
        ("Deals history", r"/dashboard/deals"),
        ("Portfolio", r"/dashboard/portfolio/list"),
        ("Exchange accounts", r"/dashboard/exchange"),
        ("Profile & Telegram", r"/dashboard/profile/?"),
        ("Memberships", r"/dashboard/membership"),
        ("Help Center", r"^https://gtprotocol\.crunch\.help/en/gt-app"),
        ("TG Community Chat", r"^https://t\.me/\+cNED563xjghkZjgy"),
    ],
)
def test_sidebar_links(marketplace_page, label: str, expected_url_pattern: str) -> None:
    allure.dynamic.title(f"Marketplace: sidebar item '{label}' opens the correct destination")
    target = marketplace_page.sidebar_item(label)
    marketplace_page.assert_redirect_destination(
        target,
        expected_url_pattern,
        f"Open sidebar item '{label}'",
    )

    if label == "TOP Traders":
        marketplace_page.assert_backtest_new_badge_visible()


@allure.feature("Marketplace")
@allure.story("Sidebar Links")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Marketplace: Backtest sidebar item shows the NEW badge and opens Backtest")
def test_sidebar_backtest_link(marketplace_page) -> None:
    marketplace_page.assert_backtest_new_badge_visible()
    target = marketplace_page.sidebar_item("Backtest")
    marketplace_page.assert_redirect_destination(
        target,
        r"^https://backtest\.gt-protocol\.io/?",
        "Open sidebar item 'Backtest'",
    )


@allure.feature("Marketplace")
@allure.story("Header Navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Marketplace: Home header control is visible and can be clicked")
def test_home_header_control_is_visible_and_clickable(marketplace_page) -> None:
    target = marketplace_page.assert_header_item_visible("Home")
    destination_url, _ = marketplace_page.assert_redirect_destination(
        target,
        r".+",
        "Click header control 'Home'",
    )
    assert destination_url, "Expected click handler on Home control to produce a destination or keep current page."
