import allure


def attach_input_payload(payload: dict[str, str]) -> None:
    rendered = "\n".join(f"{k}: {v!r}" for k, v in payload.items())
    allure.attach(rendered, "input_payload", allure.attachment_type.TEXT)


def attach_expected_actual(expected: str, actual: str) -> None:
    allure.attach(expected, "expected_check", allure.attachment_type.TEXT)
    allure.attach(actual, "actual_check", allure.attachment_type.TEXT)
