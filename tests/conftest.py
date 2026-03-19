import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(1, str(PROJECT_ROOT))

from settings import get_settings
from src.utils.telegram_reporter import (
    FailureEntry,
    SessionReport,
    build_report_from_allure,
    build_command,
    build_failure_message,
    now,
    send_report_variants,
)


_settings = get_settings()

BASE_URL = (_settings.base_url or "").strip()
HEADLESS = os.getenv("HEADLESS", "1") != "0"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
)


_TEST_OUTCOMES: dict[str, tuple[str, str]] = {}
_FAILURES: list[FailureEntry] = []
_SESSION_STARTED_AT = now()
_SESSION_STARTED_AT_MS = int(time.time() * 1000)


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-crash-reporter",
        "--disable-crashpad",
        "--noerrdialogs",
    ]
    last_error: Exception | None = None
    browser: Browser | None = None
    launch_env = os.environ.copy()
    isolated_home = tempfile.mkdtemp(prefix="pw-home-", dir="/tmp")
    launch_env["HOME"] = isolated_home
    launch_variants = [
        {
            "headless": HEADLESS,
            "slow_mo": SLOW_MO,
            "args": launch_args,
            "env": launch_env,
        },
        # On some macOS environments Playwright headless shell crashes with SIGTRAP.
        # Fallback to the full Chromium channel, which is more stable there.
        {
            "headless": HEADLESS,
            "slow_mo": SLOW_MO,
            "args": launch_args,
            "env": launch_env,
            "channel": "chromium",
        },
    ]
    for launch_options in launch_variants:
        for _ in range(4):
            try:
                browser = playwright_instance.chromium.launch(**launch_options)
                break
            except Exception as error:  # pragma: no cover - environment-dependent fallback
                last_error = error
                time.sleep(1.5)
        if browser is not None:
            break

    if browser is None:
        raise RuntimeError(f"Could not launch Playwright browser: {last_error}") from last_error

    try:
        yield browser
    finally:
        browser.close()
        shutil.rmtree(isolated_home, ignore_errors=True)


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        user_agent=USER_AGENT,
        locale="en-US",
    )
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    page.set_default_timeout(20_000)
    yield page


@pytest.fixture(scope="session")
def base_url() -> str:
    if not BASE_URL:
        pytest.skip("GT_BASE_URL is not set")
    return BASE_URL


@pytest.fixture(scope="session")
def auth_email() -> str:
    value = _settings.auth_email or ""
    if not value:
        pytest.skip("GT_AUTH_EMAIL is not set")
    return value


@pytest.fixture(scope="session")
def auth_password() -> str:
    value = _settings.auth_password or ""
    if not value:
        pytest.skip("GT_AUTH_PASSWORD is not set")
    return value


@pytest.fixture(scope="session")
def binance_api_key() -> str:
    value = _settings.binance_api_key or ""
    if not value:
        pytest.skip("GT_BINANCE_API_KEY is not set")
    return value


@pytest.fixture(scope="session")
def binance_api_secret() -> str:
    value = _settings.binance_api_secret or ""
    if not value:
        pytest.skip("GT_BINANCE_API_SECRET is not set")
    return value


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()

    if report.when == "setup":
        if report.failed:
            _TEST_OUTCOMES[item.nodeid] = ("failed", report.when)
            _FAILURES.append(
                FailureEntry(
                    nodeid=item.nodeid,
                    phase=report.when,
                    message=build_failure_message(report.longrepr),
                )
            )
        elif report.skipped:
            _TEST_OUTCOMES[item.nodeid] = ("skipped", report.when)
    elif report.when == "call":
        if getattr(report, "wasxfail", False):
            status = "xpassed" if report.passed else "xfailed"
        elif report.failed:
            status = "failed"
        elif report.skipped:
            status = "skipped"
        else:
            status = "passed"
        _TEST_OUTCOMES[item.nodeid] = (status, report.when)
        if report.failed:
            _FAILURES.append(
                FailureEntry(
                    nodeid=item.nodeid,
                    phase=report.when,
                    message=build_failure_message(report.longrepr),
                )
            )
    elif report.when == "teardown" and report.failed:
        _TEST_OUTCOMES[item.nodeid] = ("error", report.when)
        _FAILURES.append(
            FailureEntry(
                nodeid=item.nodeid,
                phase=report.when,
                message=build_failure_message(report.longrepr),
            )
        )

    if report.passed:
        return
    if report.when not in {"setup", "call", "teardown"}:
        return

    page: Page | None = item.funcargs.get("page") if hasattr(item, "funcargs") else None
    if page is None:
        return

    try:
        screenshot = page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=f"{item.name}_{report.when}_failure_screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as error:  # pragma: no cover - best effort failure diagnostics
        allure.attach(
            str(error),
            name=f"{item.name}_{report.when}_screenshot_error",
            attachment_type=allure.attachment_type.TEXT,
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _settings.telegram_enabled:
        return

    token = (_settings.telegram_bot_token or "").strip()
    chat_id = (_settings.telegram_chat_id or "").strip()
    if not token or not chat_id:
        return

    report = build_report_from_allure(
        project_name=_settings.telegram_project_name,
        command=build_command(),
        base_url=BASE_URL,
        results_dir="allure-results",
        min_start_time_ms=_SESSION_STARTED_AT_MS,
        exit_status=int(exitstatus),
    )
    if report is None:
        report = SessionReport(
            project_name=_settings.telegram_project_name,
            command=build_command(),
            base_url=BASE_URL,
            collected=session.testscollected,
            duration_seconds=now() - _SESSION_STARTED_AT,
            exit_status=int(exitstatus),
        )

        for status, _phase in _TEST_OUTCOMES.values():
            if status == "passed":
                report.passed += 1
            elif status == "failed":
                report.failed += 1
            elif status == "skipped":
                report.skipped += 1
            elif status == "xfailed":
                report.xfailed += 1
            elif status == "xpassed":
                report.xpassed += 1
            elif status == "error":
                report.errors += 1

        report.failures.extend(_FAILURES)

    variants = _settings.telegram_report_variants.split(",")
    try:
        sent_variants = send_report_variants(
            token=token,
            chat_id=chat_id,
            report=report,
            variants=variants,
            verify_ssl=_settings.telegram_verify_ssl,
        )
        terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is not None:
            terminal_reporter.write_line(
                f"Telegram report sent to chat {chat_id} with variants: {', '.join(sent_variants)}"
            )
    except Exception as error:  # pragma: no cover - network-dependent integration
        terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is not None:
            terminal_reporter.write_line(f"Telegram report failed: {error}", red=True)
