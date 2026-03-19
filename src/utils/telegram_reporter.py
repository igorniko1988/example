from __future__ import annotations

import html
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class FailureEntry:
    nodeid: str
    phase: str
    message: str
    title: str = ""
    feature: str = ""
    story: str = ""
    last_steps: list[str] = field(default_factory=list)


@dataclass
class SessionReport:
    project_name: str
    command: str
    base_url: str
    collected: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    exit_status: int = 0
    failures: list[FailureEntry] = field(default_factory=list)
    passed_titles: list[str] = field(default_factory=list)

    @property
    def total_finished(self) -> int:
        return self.passed + self.failed + self.skipped + self.xfailed + self.xpassed + self.errors

    @property
    def overall_status(self) -> str:
        return "FAILED" if self.failed or self.errors or self.exit_status else "PASSED"


def send_report_variants(
    *,
    token: str,
    chat_id: str,
    report: SessionReport,
    variants: Iterable[str],
    verify_ssl: bool = True,
) -> list[str]:
    sent_variants: list[str] = []
    for variant in _normalize_variants(variants):
        if variant == "rich_failures" and not report.failures:
            continue
        if variant == "failures" and not report.failures:
            continue
        send_telegram_message(
            token=token,
            chat_id=chat_id,
            text=render_report(report, variant),
            verify_ssl=verify_ssl,
        )
        sent_variants.append(variant)
    return sent_variants


def render_report(report: SessionReport, variant: str) -> str:
    if variant == "compact":
        return _render_compact(report)
    if variant == "detailed":
        return _render_detailed(report)
    if variant == "failures":
        return _render_failures(report)
    if variant == "rich":
        return _render_rich(report)
    if variant == "rich_counts":
        return _render_rich_counts(report)
    if variant == "rich_failures":
        return _render_rich_failures(report)
    raise ValueError(f"Unsupported telegram report variant: {variant}")


def send_telegram_message(*, token: str, chat_id: str, text: str, verify_ssl: bool = True) -> None:
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url=f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            ssl_context = None
            if not verify_ssl:
                ssl_context = ssl._create_unverified_context()
            with urllib.request.urlopen(request, timeout=15, context=ssl_context) as response:
                response.read()
            return
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram API returned HTTP {error.code}: {body}") from error
        except urllib.error.URLError as error:
            last_error = error
            if attempt == 2:
                raise RuntimeError(f"Telegram API request failed: {error.reason}") from error
            time.sleep(1.5)

    if last_error is not None:
        raise RuntimeError(f"Telegram API request failed: {last_error}") from last_error


def _normalize_variants(variants: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for variant in variants:
        name = variant.strip().lower()
        if not name or name in normalized:
            continue
        normalized.append(name)
    return normalized or ["compact"]


def _render_compact(report: SessionReport) -> str:
    lines = [
        f"<b>{_escape(report.project_name)} | Variant: compact</b>",
        f"Status: <b>{report.overall_status}</b>",
        f"Totals: {report.total_finished}/{report.collected} finished",
        (
            f"Passed: {report.passed} | Failed: {report.failed} | Errors: {report.errors} | "
            f"Skipped: {report.skipped}"
        ),
        f"Duration: {_format_duration(report.duration_seconds)}",
        f"Base URL: <code>{_escape(report.base_url)}</code>",
    ]
    if report.failures:
        lines.append("Top failures:")
        for index, failure in enumerate(report.failures[:3], start=1):
            title = failure.title or failure.nodeid
            lines.append(f"{index}. {_escape(title)}")
            if failure.feature or failure.story:
                lines.append(f"   {_escape(' / '.join(part for part in [failure.feature, failure.story] if part))}")
            lines.append(f"   <code>{_escape(_truncate(failure.message, 120))}</code>")
    return "\n".join(lines)


def _render_detailed(report: SessionReport) -> str:
    lines = [
        f"<b>{_escape(report.project_name)} | Variant: detailed</b>",
        f"Status: <b>{report.overall_status}</b>",
        f"Command: <code>{_escape(report.command)}</code>",
        f"Base URL: <code>{_escape(report.base_url)}</code>",
        f"Collected: {report.collected}",
        f"Passed: {report.passed}",
        f"Failed: {report.failed}",
        f"Errors: {report.errors}",
        f"Skipped: {report.skipped}",
        f"XFailed: {report.xfailed}",
        f"XPassed: {report.xpassed}",
        f"Duration: {_format_duration(report.duration_seconds)}",
    ]
    if report.failures:
        lines.append("Failure details:")
        for index, failure in enumerate(report.failures[:5], start=1):
            title = failure.title or failure.nodeid
            lines.append(f"{index}. {_escape(title)}")
            if failure.feature or failure.story:
                lines.append(f"   group: {_escape(' / '.join(part for part in [failure.feature, failure.story] if part))}")
            lines.append(f"   phase: {_escape(failure.phase)}")
            lines.append(f"   error: <code>{_escape(_truncate(failure.message, 220))}</code>")
            if failure.last_steps:
                lines.append(f"   last steps: {_escape(' -> '.join(failure.last_steps[:3]))}")
    return "\n".join(lines)


def _render_failures(report: SessionReport) -> str:
    lines = [
        f"<b>{_escape(report.project_name)} | Variant: failures</b>",
        f"Status: <b>{report.overall_status}</b>",
        f"Failed: {report.failed} | Errors: {report.errors} | Duration: {_format_duration(report.duration_seconds)}",
    ]
    if not report.failures:
        lines.append("No failed tests.")
        return "\n".join(lines)

    lines.append("Failed test list:")
    for index, failure in enumerate(report.failures[:10], start=1):
        title = failure.title or failure.nodeid
        lines.append(f"{index}. {_escape(title)}")
        if failure.feature or failure.story:
            lines.append(f"   {_escape(' / '.join(part for part in [failure.feature, failure.story] if part))}")
        lines.append(f"   <code>{_escape(_truncate(failure.message, 180))}</code>")
        if failure.last_steps:
            lines.append(f"   last steps: {_escape(' -> '.join(failure.last_steps[:4]))}")
    remaining = len(report.failures) - 10
    if remaining > 0:
        lines.append(f"... and {remaining} more failures")
    return "\n".join(lines)


def _render_rich(report: SessionReport) -> str:
    return _render_rich_base(report, include_passed_list=True)


def _render_rich_counts(report: SessionReport) -> str:
    return _render_rich_base(report, include_passed_list=False)


def _render_rich_base(report: SessionReport, *, include_passed_list: bool) -> str:
    status_icon = _status_icon(report)
    headline = _headline(report)
    pass_rate = _pass_rate(report)
    lines = [
        f"{status_icon} <b>{_escape(report.project_name)}</b>",
        f"<blockquote><b>{_escape(headline)}</b>\n"
        f"<b>Pass rate</b>: {pass_rate}\n"
        f"<b>Run status</b>: {_escape(report.overall_status)}\n"
        f"<b>Duration</b>: {_format_duration(report.duration_seconds)}\n"
        f"<b>Environment</b>: <code>{_escape(report.base_url)}</code>\n"
        f"<b>Command</b>: <code>{_escape(_truncate(report.command, 120))}</code></blockquote>",
        (
            "<pre>"
            f"🟢 PASS   {report.passed}\n"
            f"🔴 FAIL   {report.failed}\n"
            f"🟠 ERROR  {report.errors}\n"
            f"🟡 SKIP   {report.skipped}\n"
            f"📦 TOTAL  {report.collected}\n"
            f"⏱ TIME   {_format_duration(report.duration_seconds)}"
            "</pre>"
        ),
    ]
    if report.failures:
        lines.append("<b>Needs attention</b>")
        for index, failure in enumerate(report.failures[:2], start=1):
            title = failure.title or failure.nodeid
            group = " / ".join(part for part in [failure.feature, failure.story] if part)
            failure_block = [f"{index}. <b>{_escape(title)}</b>"]
            if group:
                failure_block.append(_escape(group))
            failure_block.append(_escape(_truncate(failure.message, 180)))
            if failure.last_steps:
                failure_block.append(f"Last step: {_escape(_truncate(failure.last_steps[-1], 140))}")
            lines.append("<blockquote>" + "\n".join(failure_block) + "</blockquote>")
    else:
        lines.append("<blockquote>No failed tests.</blockquote>")

    if include_passed_list and report.passed_titles:
        lines.append("<b>Completed successfully</b>")
        lines.append(_render_passed_block(report.passed_titles, current_lines=lines))
    return _truncate_message("\n".join(lines))


def _render_rich_failures(report: SessionReport) -> str:
    status_icon = _status_icon(report)
    pass_rate = _pass_rate(report)
    lines = [
        f"{status_icon} <b>{_escape(report.project_name)} | Failure Digest</b>",
        f"<blockquote><b>Passed</b>: {report.passed}/{report.collected} ({pass_rate})\n"
        f"<b>Needs attention</b>: {report.failed + report.errors}\n"
        f"<b>Duration</b>: {_format_duration(report.duration_seconds)}</blockquote>",
    ]
    if not report.failures:
        lines.append("<blockquote>No failed tests.</blockquote>")
        return _truncate_message("\n".join(lines))

    for index, failure in enumerate(report.failures[:4], start=1):
        title = failure.title or failure.nodeid
        group = " / ".join(part for part in [failure.feature, failure.story] if part)
        lines.append(f"<b>{index}. {_escape(_truncate(title, 110))}</b>")
        body = []
        if group:
            body.append(_escape(group))
        body.append(_escape(_truncate(failure.message, 220)))
        if failure.last_steps:
            body.append("Recent steps:")
            for step in failure.last_steps[-3:]:
                body.append(f"• {_escape(_truncate(step, 110))}")
        lines.append("<blockquote>" + "\n".join(body) + "</blockquote>")
    remaining = len(report.failures) - 4
    if remaining > 0:
        lines.append(f"<i>... and {remaining} more failures</i>")
    return _truncate_message("\n".join(lines))


def build_failure_message(longrepr: object) -> str:
    if isinstance(longrepr, tuple):
        return " | ".join(str(part) for part in longrepr if part)
    if longrepr is None:
        return ""
    if hasattr(longrepr, "reprcrash") and getattr(longrepr, "reprcrash", None):
        reprcrash = longrepr.reprcrash
        return f"{reprcrash.message} ({reprcrash.path}:{reprcrash.lineno})"
    return str(longrepr)


def build_command(argv: list[str] | None = None) -> str:
    parts = argv or sys.argv
    return " ".join(parts)


def now() -> float:
    return time.monotonic()


def build_report_from_allure(
    *,
    project_name: str,
    command: str,
    base_url: str,
    results_dir: str | os.PathLike[str],
    min_start_time_ms: int | None = None,
    exit_status: int = 0,
) -> SessionReport | None:
    result_files = sorted(Path(results_dir).glob("*-result.json"))
    if not result_files:
        return None

    report = SessionReport(
        project_name=project_name,
        command=command,
        base_url=base_url,
        exit_status=exit_status,
    )

    latest_stop = 0
    earliest_start = 0
    for file_path in result_files:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        started = int(data.get("start") or 0)
        if min_start_time_ms is not None and started and started < min_start_time_ms:
            continue

        status = data.get("status", "unknown")
        report.collected += 1
        latest_stop = max(latest_stop, int(data.get("stop") or 0))
        if started:
            earliest_start = started if earliest_start == 0 else min(earliest_start, started)
        if status == "passed":
            report.passed += 1
            title = data.get("name") or data.get("fullName") or file_path.name
            report.passed_titles.append(str(title))
        elif status == "failed":
            report.failed += 1
        elif status == "skipped":
            report.skipped += 1
        elif status == "broken":
            report.errors += 1
        elif status == "unknown":
            report.errors += 1

        if status not in {"failed", "broken"}:
            continue

        report.failures.append(
            FailureEntry(
                nodeid=data.get("fullName") or file_path.name,
                phase="call" if status == "failed" else "broken",
                message=_allure_failure_message(data),
                title=data.get("name") or data.get("fullName") or file_path.name,
                feature=_allure_label(data, "feature"),
                story=_allure_label(data, "story"),
                last_steps=_last_failed_steps(data.get("steps", [])),
            )
        )

    if report.collected == 0:
        return None

    if latest_stop and earliest_start:
        report.duration_seconds = max(0.0, (latest_stop - earliest_start) / 1000)
    return report


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _escape(value: str) -> str:
    return html.escape(value, quote=False)


def _truncate_message(value: str, limit: int = 4096) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 20] + "\n<i>Message truncated</i>"


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _render_passed_block(passed_titles: list[str], current_lines: list[str], limit: int = 4096) -> str:
    unique_titles = _unique_preserve_order(passed_titles)
    prefix = "<blockquote>"
    suffix = "</blockquote>"
    base_text = "\n".join(current_lines) + "\n" + prefix
    current_len = len(base_text) + len(suffix)

    rendered_items: list[str] = []
    used = 0
    for title in unique_titles:
        candidate = f"• {_escape(_truncate(title, 120))}"
        extra_len = len(candidate) + (1 if rendered_items else 0)
        if current_len + extra_len > limit - 80:
            break
        rendered_items.append(candidate)
        current_len += extra_len
        used += 1

    remaining = len(unique_titles) - used
    if remaining > 0:
        rendered_items.append(f"• ... and {remaining} more passed")

    return prefix + "\n".join(rendered_items) + suffix


def _pass_rate(report: SessionReport) -> str:
    if report.collected <= 0:
        return "n/a"
    return f"{(report.passed / report.collected) * 100:.0f}%"


def _status_icon(report: SessionReport) -> str:
    if report.failed == 0 and report.errors == 0:
        return "✅"
    if report.collected > 0 and (report.passed / report.collected) >= 0.8:
        return "🟡"
    return "❌"


def _headline(report: SessionReport) -> str:
    if report.failed == 0 and report.errors == 0:
        return f"All checks passed: {report.passed}/{report.collected}"
    if report.collected > 0 and (report.passed / report.collected) >= 0.8:
        return f"Mostly green: {report.passed}/{report.collected} passed"
    return f"Run needs attention: {report.passed}/{report.collected} passed"


def _allure_label(data: dict, name: str) -> str:
    for label in data.get("labels", []):
        if label.get("name") == name:
            return str(label.get("value") or "")
    return ""


def _allure_failure_message(data: dict) -> str:
    status_details = data.get("statusDetails") or {}
    message = status_details.get("message") or ""
    if message:
        return message
    return data.get("status", "failed")


def _last_failed_steps(steps: list[dict]) -> list[str]:
    flat_steps: list[str] = []

    def walk(items: list[dict]) -> None:
        for step in items:
            name = str(step.get("name") or "").strip()
            status = str(step.get("status") or "").strip()
            if name:
                flat_steps.append(f"{name} [{status}]")
            nested = step.get("steps") or []
            if nested:
                walk(nested)

    walk(steps)
    return flat_steps[-4:]
