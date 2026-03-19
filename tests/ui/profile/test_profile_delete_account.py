import allure
from playwright.sync_api import expect


@allure.feature("Profile")
@allure.story("Delete Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Delete Account' heading and action button are visible")
def test_delete_account_section_is_visible(logged_in_profile_page) -> None:
    expect(logged_in_profile_page.heading("Delete Account", level=5)).to_be_visible()
    expect(logged_in_profile_page.delete_account_button()).to_be_visible()
    expect(logged_in_profile_page.delete_account_button()).to_be_enabled()


@allure.feature("Profile")
@allure.story("Delete Account")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Profile: delete-account modal shows warnings, checkboxes, progress and disabled delete button by default")
def test_delete_account_modal_default_state(logged_in_profile_page) -> None:
    logged_in_profile_page.open_delete_account_modal()

    modal = logged_in_profile_page.delete_account_modal()
    expect(modal.get_by_role("heading", name="Deleting Your Account")).to_be_visible()
    expect(modal.get_by_text("This action is permanent and cannot be undone")).to_be_visible()
    expect(modal.get_by_text("Please note:")).to_be_visible()
    expect(modal.get_by_text("Deleting your account will terminate your current membership.")).to_be_visible()
    expect(modal.get_by_text("All your data will be permanently deleted and cannot be restored")).to_be_visible()
    expect(modal.get_by_text("Before deleting, please make sure:")).to_be_visible()
    expect(modal.get_by_text("0 of 4 steps completed")).to_be_visible()
    expect(logged_in_profile_page.delete_account_confirm_button()).to_be_disabled()


@allure.feature("Profile")
@allure.story("Delete Account")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Profile: ticking all delete-account checkboxes enables the destructive action")
def test_delete_account_modal_enables_action_after_all_checkboxes(logged_in_profile_page) -> None:
    logged_in_profile_page.open_delete_account_modal()
    logged_in_profile_page.tick_all_delete_modal_checkboxes()

    expect(logged_in_profile_page.delete_modal_progress_text()).to_have_text("4 of 4 steps completed")
    expect(logged_in_profile_page.delete_account_confirm_button()).to_be_enabled()


@allure.feature("Profile")
@allure.story("Delete Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: 'Keep my account' closes the delete-account modal")
def test_delete_account_modal_keep_my_account_closes_it(logged_in_profile_page) -> None:
    logged_in_profile_page.open_delete_account_modal()
    logged_in_profile_page.close_delete_modal_with_keep_account()
    expect(logged_in_profile_page.heading("My Profile", level=1)).to_be_visible()


@allure.feature("Profile")
@allure.story("Delete Account")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile: modal close button closes the delete-account modal")
def test_delete_account_modal_close_button_works(logged_in_profile_page) -> None:
    logged_in_profile_page.open_delete_account_modal()
    logged_in_profile_page.close_delete_modal_with_close_button()
