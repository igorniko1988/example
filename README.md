# GT Protocol UI Test Suite

UI end-to-end test suite for GT Protocol web flows built on `pytest`, `Playwright`, and `Allure`.

The suite covers critical user journeys around:
- authentication
- registration validation
- Binance exchange connection
- Marketplace regression checks
- demo strategy flow
- real futures strategy flows

## Stack

- Python 3.12
- `pytest`
- `playwright`
- `allure-pytest`
- `pydantic-settings`

## Repository Layout

```text
.
├── src/pages/                     # Page objects and flow helpers
├── src/utils/                     # Allure and Telegram reporting helpers
├── tests/conftest.py              # Shared fixtures, browser lifecycle, pytest hooks
├── tests/ui/auth/                 # Auth and registration tests
├── tests/ui/exchange/             # Exchange account tests
├── tests/ui/marketplace_regression/ # Marketplace regression coverage
├── tests/ui/strategy/             # Demo and real futures strategy tests
├── settings.py                    # Environment-backed runtime settings
├── pytest.ini                     # Pytest defaults, including Allure output
└── .env.example                   # Example environment configuration
```

## Prerequisites

- Python 3.12 available locally
- A working virtual environment in `.venv`
- Playwright browser dependencies installed for the environment
- Access to a valid GT Protocol test account
- Valid Binance API credentials for exchange and real futures scenarios

## Setup

Create and activate the virtual environment if needed:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Prepare the environment file:

```bash
cp .env.example .env
```

Fill in the required values in `.env`.

## Environment Variables

All runtime settings are loaded from `.env` with the `GT_` prefix.
There is no hardcoded fallback for `GT_BASE_URL`; set it explicitly for each environment.

Required for most authenticated UI scenarios:

```env
GT_BASE_URL=https://app.gt-protocol.io
GT_AUTH_EMAIL=your_email@example.com
GT_AUTH_PASSWORD=your_password_here
```

Required for exchange and real futures tests:

```env
GT_BINANCE_API_KEY=your_binance_api_key
GT_BINANCE_API_SECRET=your_binance_api_secret
```

Optional Telegram reporting:

```env
GT_TELEGRAM_ENABLED=false
GT_TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GT_TELEGRAM_CHAT_ID=your_telegram_chat_id
GT_TELEGRAM_REPORT_VARIANTS=rich_counts
GT_TELEGRAM_PROJECT_NAME=GT UI Tests
GT_TELEGRAM_VERIFY_SSL=true
```

Notes:
- `GT_TELEGRAM_REPORT_VARIANTS=rich_counts` sends the compact final report without listing all passed checks.
- `GT_TELEGRAM_REPORT_VARIANTS=rich` sends the detailed report with passed-check names.
- `GT_TELEGRAM_REPORT_VARIANTS=rich,rich_failures` sends the main report and a separate failure digest when failures exist.
- `GT_TELEGRAM_VERIFY_SSL=false` can be used only when the local machine has a broken SSL chain to Telegram. Do not use it unless needed.

## Running Tests

Run the full UI suite:

```bash
source .venv/bin/activate
pytest tests/ui
```

Run a single test module:

```bash
pytest tests/ui/strategy/test_real_futures_strategy_lifecycle.py
```

Run a single test:

```bash
pytest tests/ui/exchange/test_exchange_account_lifecycle.py::test_binance_exchange_account_add_and_delete_with_frontend_confirmations
```

Useful runtime flags:

```bash
HEADLESS=1 pytest tests/ui
SLOW_MO=250 pytest tests/ui/auth/test_authorization_login.py
```

Run the smoke suite only:

```bash
pytest -m smoke tests/ui
```

## Allure Reporting

Pytest writes Allure artifacts to `allure-results/` by default via `pytest.ini`.

Example:

```bash
pytest tests/ui
```

This produces raw Allure result files under:

```text
allure-results/
```

If the local machine has the Allure CLI installed, you can render the report with:

```bash
allure serve allure-results
```

In GitHub Actions, the `UI Smoke` workflow:
- uploads raw `allure-results`
- uploads rendered `allure-report` HTML as an artifact
- publishes the latest smoke Allure report to GitHub Pages on `push` to `main` and on manual runs
- generates Allure HTML directly with the Allure CLI instead of the deprecated Docker-based report action

To view the Pages report, enable GitHub Pages in the repository settings and set the source to `GitHub Actions`.

Required repository secrets for authenticated smoke runs:
- `GT_BASE_URL`
- `GT_AUTH_EMAIL`
- `GT_AUTH_PASSWORD`

## Telegram Reporting

Telegram reporting is executed automatically at the end of the pytest session in `pytest_sessionfinish`.

Behavior:
- the report is built from fresh `allure-results`
- if Allure results are unavailable, the code falls back to pytest counters
- the message is sent only when `GT_TELEGRAM_ENABLED=true` and both bot credentials are configured
- `rich_failures` is sent only when there are actual failures

Recommended default:

```env
GT_TELEGRAM_ENABLED=false
GT_TELEGRAM_REPORT_VARIANTS=rich_counts
```

This keeps the report short and readable for a group chat while still showing:
- pass rate
- total passed / failed / skipped
- duration
- failed checks requiring attention

## Test Design Conventions

The suite follows a few explicit conventions:

- `@allure.title(...)` describes the user-facing scenario and expected result.
- `@allure.story(...)` groups tests by business behavior, not by implementation detail.
- `allure.step(...)` should read like an audit trail for a QA engineer reviewing the run.
- Cleanup is best-effort, but cleanup failures are attached to Allure instead of silently swallowed.
- Page objects own UI interaction details; tests should stay scenario-focused.

## Troubleshooting

### `ModuleNotFoundError: No module named 'allure'`

Usually this means the virtual environment is not activated correctly or dependencies were not installed into the current `.venv`.

Use:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### `pytest` or `pip` points to an old directory after moving the repo

If the project directory was renamed or moved, stale virtualenv launcher scripts may still point to the previous path. Recreate the venv if needed:

```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Telegram report did not arrive

Check the following:
- the bot token is valid
- the bot is added to the target group
- `GT_TELEGRAM_CHAT_ID` is correct
- the machine can reach `api.telegram.org`
- pytest output does not contain `Telegram report failed`

### Exchange or strategy tests are unstable

These scenarios depend on live backend behavior and external exchange/account state. Before debugging code, verify:
- the test account is valid
- the Binance credentials are active
- there are no leftover connected exchanges or strategies from earlier runs

## Current Coverage

Current UI test coverage includes:
- successful login
- protected profile access after login
- registration validation
- Binance connect form validation
- Binance account connection and deletion
- Marketplace shell, navigation, strategy cards, and copy/details flows
- demo strategy end-to-end flow
- real futures strategy end-to-end flow

## Maintenance Notes

- Keep Allure titles and stories stable and readable; they are reused in Telegram reporting.
- Prefer improving page objects over adding brittle sleeps in tests.
- When adding a new scenario, decide first whether it belongs in `auth`, `exchange`, `marketplace_regression`, or `strategy`.
- If a scenario requires live external state, make cleanup explicit and observable in Allure.
