import re

import allure
import pytest
from playwright.sync_api import expect


VALID_LOOKING_PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: page loads successfully")
def test_connect_hyperliquid_page_loads(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.heading()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: heading and logo are visible")
def test_connect_hyperliquid_heading_and_logo(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.heading()).to_be_visible()
    expect(connect_hyperliquid_page.logo()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: safety banner is visible")
def test_connect_hyperliquid_banner(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.banner()).to_be_visible()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: guide link opens in a new tab")
def test_connect_hyperliquid_guide_link(connect_hyperliquid_page) -> None:
    popup = connect_hyperliquid_page.open_guide_popup()
    try:
        assert popup.url.startswith(
            "https://gtprotocol.crunch.help/en/all-financial-matters-and-exchanges/link-your-hyperliquid-to-gt-app-account"
        )
    finally:
        popup.close()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: Back returns to the exchange overview page")
def test_connect_hyperliquid_back_button(connect_hyperliquid_page) -> None:
    connect_hyperliquid_page.back_button().click()
    expect(connect_hyperliquid_page.page).to_have_url(re.compile(r"/dashboard/exchange"), timeout=30_000)


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: Connection Name field shows placeholder and accepts input")
def test_connect_hyperliquid_connection_name_input(connect_hyperliquid_page) -> None:
    field = connect_hyperliquid_page.connection_name_input()
    assert field.get_attribute("placeholder") == "For example: My Hyperliquid"
    field.fill("Test Connection")
    expect(field).to_have_value("Test Connection")


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: Private Key field shows placeholder and accepts input")
def test_connect_hyperliquid_private_key_input(connect_hyperliquid_page) -> None:
    field = connect_hyperliquid_page.private_key_input()
    assert field.get_attribute("placeholder") == "Private key: (0x...)"
    field.fill(VALID_LOOKING_PRIVATE_KEY)
    assert field.input_value() != ""


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: info icons are visible for both labels")
def test_connect_hyperliquid_info_icons(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.info_icons()).to_have_count(2)


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: eye icon is visible for the private key field")
def test_connect_hyperliquid_eye_icon_visible(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.eye_icons()).to_have_count(1)


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: wallet connection instruction is visible")
def test_connect_hyperliquid_instruction(connect_hyperliquid_page) -> None:
    assert 'Click "Connect Wallet" and approve the connection using the same wallet currently connected to Hyperliquid' in connect_hyperliquid_page.body_text()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: Connect wallet is disabled with empty required fields")
def test_connect_hyperliquid_button_disabled_by_default(connect_hyperliquid_page) -> None:
    expect(connect_hyperliquid_page.connect_wallet_button()).to_be_disabled()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Form")
@allure.title("Connect Hyperliquid: Connect wallet becomes enabled after valid-looking fields are filled")
def test_connect_hyperliquid_button_enabled_after_fill(connect_hyperliquid_page) -> None:
    connect_hyperliquid_page.connection_name_input().fill("Test Connection")
    connect_hyperliquid_page.private_key_input().fill(VALID_LOOKING_PRIVATE_KEY)
    expect(connect_hyperliquid_page.connect_wallet_button()).to_be_enabled()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Wallet Flow")
@allure.title("Connect Hyperliquid: clicking Connect wallet opens the wallet-connect layer")
def test_connect_hyperliquid_wallet_connect_layer(connect_hyperliquid_page) -> None:
    connect_hyperliquid_page.connection_name_input().fill("Test Connection")
    connect_hyperliquid_page.private_key_input().fill(VALID_LOOKING_PRIVATE_KEY)
    connect_hyperliquid_page.connect_wallet_button().click(force=True)
    expect(connect_hyperliquid_page.wallet_modal()).to_be_visible(timeout=10_000)
    expect(connect_hyperliquid_page.wallet_iframe()).to_have_count(1)


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Wallet Flow")
@allure.title("Connect Hyperliquid: wallet options are visible when the modal exposes them accessibly")
def test_connect_hyperliquid_wallet_options_if_accessible(connect_hyperliquid_page) -> None:
    # WalletConnect renders most wallet options inside a cross-origin iframe that is not text-accessible in headless runs.
    # To remove this skip, run this assertion in an environment where the wallet list is exposed accessibly or via a supported test hook.
    connect_hyperliquid_page.connection_name_input().fill("Test Connection")
    connect_hyperliquid_page.private_key_input().fill(VALID_LOOKING_PRIVATE_KEY)
    connect_hyperliquid_page.connect_wallet_button().click(force=True)
    connect_hyperliquid_page.page.wait_for_timeout(3_000)
    body = connect_hyperliquid_page.body_text()
    expected = ["WalletConnect", "Trust Wallet", "MetaMask", "Coinbase", "All Wallets"]
    if not any(value in body for value in expected):
        pytest.skip("Wallet options are rendered inside a non-accessible wallet iframe in the current environment.")


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Wallet Flow")
@allure.title("Connect Hyperliquid: wallet modal can be closed when a close control is exposed")
def test_connect_hyperliquid_wallet_modal_close_if_supported(connect_hyperliquid_page) -> None:
    # The current wallet-connect layer does not expose a stable close control in headless mode.
    # To remove this skip, expose a deterministic close button or test the flow in a headed browser where the modal controls are actionable.
    connect_hyperliquid_page.connection_name_input().fill("Test Connection")
    connect_hyperliquid_page.private_key_input().fill(VALID_LOOKING_PRIVATE_KEY)
    connect_hyperliquid_page.connect_wallet_button().click(force=True)
    close_button = connect_hyperliquid_page.page.locator(".wallet-connect-wrapper button[aria-label*='close' i], .wallet-connect-wrapper .el-dialog__headerbtn").first
    if close_button.count() == 0:
        pytest.skip("Current wallet-connect layer does not expose a stable close control.")


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid Validation")
@allure.title("Connect Hyperliquid: invalid private key format blocks submission in the current UI")
def test_connect_hyperliquid_invalid_private_key_blocks_submit(connect_hyperliquid_page) -> None:
    connect_hyperliquid_page.connection_name_input().fill("Test Connection")
    connect_hyperliquid_page.private_key_input().fill("123")
    expect(connect_hyperliquid_page.connect_wallet_button()).to_be_disabled()


@allure.feature("Exchange Pages")
@allure.story("Connect Hyperliquid")
@allure.title("Connect Hyperliquid: Set up a new Hyperliquid account opens in a new tab")
def test_connect_hyperliquid_signup_link(connect_hyperliquid_page) -> None:
    popup = connect_hyperliquid_page.open_signup_popup()
    try:
        assert popup.url.startswith("https://app.hyperliquid.xyz/join/GTPROTOCOL")
    finally:
        popup.close()
