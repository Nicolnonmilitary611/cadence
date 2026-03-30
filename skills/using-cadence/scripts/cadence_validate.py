#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


ALLOWED_TOP_LEVEL_KEYS = {"plan", "issue"}
ALLOWED_ISSUE_KEYS = {
    "id",
    "sequence",
    "title",
    "scope",
    "touch_points",
    "depends_on",
    "done_when",
    "validate_by",
    "regress_by",
    "regress_timing",
    "status",
    "validate_status",
    "regress_status",
    "notes",
}

ALLOWED_STATUS = {"todo", "in_progress", "done", "blocked"}
ALLOWED_VALIDATE_STATUS = {"not_run", "in_progress", "passed", "failed"}
ALLOWED_REGRESS_STATUS = {"not_needed", "not_run", "in_progress", "passed", "failed"}
ALLOWED_REGRESS_TIMING = {"after_done", "before_fanout"}
EXECUTION_MUTABLE_FIELDS = {"status", "validate_status", "regress_status", "notes"}


def load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ValueError(f"{path}: file not found") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path}: TOML parse error: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level document must be a TOML table")
    return data


def require_nonempty_string(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: expected a non-empty string")


def require_list_of_strings(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label}: expected a string array")


def validate_issue_document(data: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    unknown_top_level = sorted(set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top_level:
        errors.append(f"{label}: unknown top-level keys: {', '.join(unknown_top_level)}")

    require_nonempty_string(data.get("plan"), f"{label}.plan", errors)

    issues = data.get("issue")
    if not isinstance(issues, list) or not issues:
        errors.append(f"{label}.issue: expected a non-empty array of issue tables")
        return errors

    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    issue_ids: list[str] = []

    for index, issue in enumerate(issues):
        issue_label = f"{label}.issue[{index}]"
        if not isinstance(issue, dict):
            errors.append(f"{issue_label}: expected a TOML table")
            continue

        unknown_issue_keys = sorted(set(issue.keys()) - ALLOWED_ISSUE_KEYS)
        if unknown_issue_keys:
            errors.append(f"{issue_label}: unknown keys: {', '.join(unknown_issue_keys)}")

        for key in ("id", "title", "scope", "done_when", "validate_by", "regress_by", "regress_timing", "notes"):
            require_nonempty_string(issue.get(key), f"{issue_label}.{key}", errors)

        for key in ("touch_points", "depends_on"):
            require_list_of_strings(issue.get(key), f"{issue_label}.{key}", errors)

        issue_id = issue.get("id")
        if isinstance(issue_id, str) and issue_id.strip():
            if issue_id in seen_ids:
                errors.append(f"{issue_label}.id: duplicate issue id {issue_id!r}")
            else:
                seen_ids.add(issue_id)
                issue_ids.append(issue_id)

        sequence = issue.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
            errors.append(f"{issue_label}.sequence: expected a positive integer")
        elif sequence in seen_sequences:
            errors.append(f"{issue_label}.sequence: duplicate sequence {sequence!r}")
        else:
            seen_sequences.add(sequence)

        status = issue.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{issue_label}.status: expected one of {sorted(ALLOWED_STATUS)}")

        validate_status = issue.get("validate_status")
        if validate_status not in ALLOWED_VALIDATE_STATUS:
            errors.append(
                f"{issue_label}.validate_status: expected one of {sorted(ALLOWED_VALIDATE_STATUS)}"
            )

        regress_status = issue.get("regress_status")
        if regress_status not in ALLOWED_REGRESS_STATUS:
            errors.append(
                f"{issue_label}.regress_status: expected one of {sorted(ALLOWED_REGRESS_STATUS)}"
            )

        regress_timing = issue.get("regress_timing")
        if regress_timing not in ALLOWED_REGRESS_TIMING:
            errors.append(
                f"{issue_label}.regress_timing: expected one of {sorted(ALLOWED_REGRESS_TIMING)}"
            )

        depends_on = issue.get("depends_on")
        if isinstance(depends_on, list):
            if issue_id in depends_on:
                errors.append(f"{issue_label}.depends_on: issue may not depend on itself")

    valid_ids = set(issue_ids)
    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        depends_on = issue.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in depends_on:
            if dep not in valid_ids:
                errors.append(f"{label}.issue[{index}].depends_on: unknown dependency {dep!r}")

    return errors


def normalize_for_execution_compare(data: dict[str, Any]) -> tuple[tuple[str, Any], tuple[tuple[str, Any], ...]]:
    top_level = tuple(sorted((key, value) for key, value in data.items() if key != "issue"))

    issues = data.get("issue", [])
    normalized_issues = []
    for issue in issues:
        if not isinstance(issue, dict):
            normalized_issues.append(tuple())
            continue
        normalized_issue = tuple(
            sorted((key, value) for key, value in issue.items() if key not in EXECUTION_MUTABLE_FIELDS)
        )
        normalized_issues.append(normalized_issue)

    return top_level, tuple(normalized_issues)


def cmd_issue(path: Path) -> int:
    data = load_toml(path)
    errors = validate_issue_document(data, str(path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"OK: issue file is valid: {path}")
    return 0


def cmd_execution_write(before: Path, after: Path) -> int:
    before_data = load_toml(before)
    after_data = load_toml(after)

    errors = []
    errors.extend(validate_issue_document(before_data, str(before)))
    errors.extend(validate_issue_document(after_data, str(after)))

    before_issues = before_data.get("issue")
    after_issues = after_data.get("issue")
    if isinstance(before_issues, list) and isinstance(after_issues, list):
        if len(before_issues) != len(after_issues):
            errors.append("execution-write: issue count changed")
        else:
            before_ids = [issue.get("id") if isinstance(issue, dict) else None for issue in before_issues]
            after_ids = [issue.get("id") if isinstance(issue, dict) else None for issue in after_issues]
            if before_ids != after_ids:
                errors.append("execution-write: issue ordering or ids changed")

    if normalize_for_execution_compare(before_data) != normalize_for_execution_compare(after_data):
        errors.append(
            "execution-write: detected changes outside status/validate_status/regress_status/notes"
        )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"OK: execution write is valid: {after}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mechanical guardrails for Cadence issue files and execution-stage write boundaries."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue_parser = subparsers.add_parser("issue", help="validate a Cadence issue TOML file")
    issue_parser.add_argument("path", type=Path)

    execution_parser = subparsers.add_parser(
        "execution-write",
        help="validate that an execution-stage write only touched allowed fields",
    )
    execution_parser.add_argument("--before", required=True, type=Path)
    execution_parser.add_argument("--after", required=True, type=Path)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "issue":
        return cmd_issue(args.path)
    if args.command == "execution-write":
        return cmd_execution_write(args.before, args.after)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
