import re

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect

from src.utils.allure_helpers import attach_expected_actual, attach_input_payload


class AuthPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open_login(self) -> None:
        with allure.step("Open the login page"):
            for attempt in range(4):
                try:
                    self.page.goto(f"{self.base_url}/auth?tab=login", wait_until="domcontentloaded")
                    break
                except PlaywrightError:
                    if re.search(r"/dashboard/", self.page.url):
                        return
                    if attempt == 3:
                        raise
                    self.page.wait_for_timeout(1000)
        with allure.step("Wait for the login form to become visible"):
            for _ in range(3):
                login_button = self.page.get_by_role("button", name="Login").first
                email_input = self.page.get_by_role("textbox", name="Email")
                password_input = self.page.get_by_role("textbox", name="Password")
                if (
                    login_button.count() > 0
                    and email_input.count() > 0
                    and password_input.count() > 0
                    and login_button.is_visible()
                ):
                    expect(email_input).to_be_visible()
                    expect(password_input).to_be_visible()
                    return

                # Some runs are redirected to dashboard due active session.
                if re.search(r"/dashboard/", self.page.url):
                    return

                self.page.reload(wait_until="domcontentloaded")
                self.page.wait_for_timeout(800)

            expect(self.page.get_by_role("button", name="Login").first).to_be_visible()
            expect(self.page.get_by_role("textbox", name="Email")).to_be_visible()
            expect(self.page.get_by_role("textbox", name="Password")).to_be_visible()

    def login(self, email: str, password: str) -> None:
        self.open_login()
        if re.search(r"/dashboard/", self.page.url):
            return
        with allure.step("Sign in with valid credentials"):
            attach_input_payload({"email": email, "password": "***"})
            self.page.get_by_role("textbox", name="Email").fill(email)
            self.page.get_by_role("textbox", name="Password").fill(password)
            self.page.get_by_role("button", name="Login").last.click()
        with allure.step("Verify the user is signed in successfully"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/"), timeout=30_000)

    def open_register(self) -> None:
        with allure.step("Open the registration page"):
            self.page.goto(f"{self.base_url}/auth?tab=register", wait_until="domcontentloaded")
        with allure.step("Wait for the registration form to become visible"):
            expect(self.page.get_by_role("heading", name="Register now")).to_be_visible()
            expect(self.page.get_by_role("textbox", name="Email")).to_be_visible()
            expect(self.page.get_by_role("textbox", name="Password")).to_be_visible()

    def submit_register_form(self, email: str, password: str) -> None:
        attach_input_payload({"email": email, "password": password})
        with allure.step(f"Enter email: {email!r}"):
            self.page.get_by_role("textbox", name="Email").fill(email)
        with allure.step(f"Enter password: {password!r}"):
            self.page.get_by_role("textbox", name="Password").fill(password)
        with allure.step("Submit the registration form"):
            self.page.get_by_role("button", name="Register").last.click()

    def assert_redirected_to_dashboard(self) -> None:
        with allure.step("Verify the user is redirected from auth to the dashboard"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/"))
            assert "/auth" not in self.page.url
            attach_expected_actual(
                "URL contains /dashboard and does not contain /auth",
                f"actual URL: {self.page.url}",
            )

    def assert_dashboard_shell_visible(self) -> None:
        with allure.step("Verify dashboard content is visible"):
            expect(self.page.locator("body")).to_contain_text(re.compile(r"TOP Traders|Portfolio|Account", re.I))

    def open_protected_profile_page(self) -> None:
        with allure.step("Navigate directly to the protected Profile page"):
            self.page.goto(f"{self.base_url}/dashboard/profile", wait_until="domcontentloaded")

    def assert_profile_page_opened_for_authenticated_user(self) -> None:
        with allure.step("Verify the Profile page opens without redirecting back to auth"):
            expect(self.page).to_have_url(re.compile(r"/dashboard/profile"))
            assert "/auth" not in self.page.url
            attach_expected_actual(
                "URL contains /dashboard/profile and does not contain /auth",
                f"actual URL: {self.page.url}",
            )

    def assert_registration_page_is_still_open(self) -> None:
        with allure.step("Verify the user remains on the registration page"):
            expect(self.page).to_have_url(re.compile(r"/auth\?tab=register"))

    def assert_required_field_errors_visible(self) -> None:
        with allure.step("Verify validation messages are shown for both required fields"):
            required_errors = self.page.get_by_text("Field is required.")
            expect(required_errors.first).to_be_visible()
            actual_errors = required_errors.all_inner_texts()
            expected_message = "Field is required."
            allure.attach("\n".join(actual_errors), "actual_validation_messages", allure.attachment_type.TEXT)
            assert len(actual_errors) >= 2
            assert all(msg.strip() == expected_message for msg in actual_errors)
            attach_expected_actual("Each error equals 'Field is required.'", f"actual: {actual_errors}")

    def assert_invalid_email_error_visible(self) -> None:
        with allure.step("Verify the invalid email validation message is shown"):
            error_locator = self.page.get_by_text(re.compile(r"Please enter( a)? valid email address\.", re.I))
            expect(error_locator).to_be_visible()
            actual_message = error_locator.first.inner_text().strip()
            normalized_actual = re.sub(r"\s+", " ", actual_message).lower()
            expected_regex = r"^please enter( a)? valid email address\.$"
            attach_expected_actual(expected_regex, actual_message)
            assert re.match(expected_regex, normalized_actual)

    def assert_password_rules_error_visible(self, expected_message: str) -> None:
        with allure.step("Verify the password policy validation message is shown"):
            error_locator = self.page.get_by_text(expected_message)
            expect(error_locator).to_be_visible()
            actual_message = error_locator.first.inner_text().strip()
            attach_expected_actual(expected_message, actual_message)
            assert actual_message == expected_message
