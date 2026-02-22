"""Live integration tests that hit a real LLM backend."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Literal

import pytest
from pydantic import BaseModel, ValidationError

from tutr.config import TutrConfig, load_config

_LAST_LIVE_CALL_AT: float | None = None
_CASES_FILE = Path(__file__).with_name("integration_live_cases.json")


def _load_live_config() -> TutrConfig:
    if os.environ.get("TUTR_RUN_INTEGRATION") != "1":
        pytest.skip("Set TUTR_RUN_INTEGRATION=1 to run live integration tests")

    override_model = os.environ.get("TUTR_INTEGRATION_MODEL") or os.environ.get("TUTR_MODEL")
    if not override_model:
        config = load_config()
        if not config.model:
            pytest.skip(
                "No model configured. Set TUTR_INTEGRATION_MODEL/TUTR_MODEL or configure tutr."
            )
        model = config.model
    else:
        model = override_model
        config = TutrConfig(model=model)

    provider = model.split("/", 1)[0] if "/" in model else None
    config.provider = provider
    provider_key = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider or "")

    api_key = os.environ.get("TUTR_INTEGRATION_API_KEY")
    if not api_key and provider_key:
        api_key = os.environ.get(provider_key)
    if not api_key:
        api_key = config.api_key

    if provider != "ollama" and not api_key:
        pytest.skip(
            "No API key found. Set TUTR_INTEGRATION_API_KEY, configure tutr with an API key, "
            f"or set the provider env key ({provider_key})."
        )

    config.api_key = api_key
    return config


def _assert_safe_single_command(command: str) -> None:
    dangerous_pattern = re.compile(
        r"(`|\$\(|\brm\b|\bmkfs\b|\bdd\b|\bshutdown\b|\breboot\b|\bkillall\b|\b:\s*\(\))",
        re.IGNORECASE,
    )
    assert "\n" not in command, f"expected a single-line command, got: {command!r}"
    assert not dangerous_pattern.search(command), f"unsafe command generated: {command!r}"


def _extract_suggested_command(stdout: str) -> str:
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("$ "):
            return stripped[2:]
    raise AssertionError(f"failed to locate suggested command in stdout:\n{stdout}")


def _has_integration_overrides() -> bool:
    return bool(
        os.environ.get("TUTR_INTEGRATION_MODEL")
        or os.environ.get("TUTR_MODEL")
        or os.environ.get("TUTR_INTEGRATION_API_KEY")
    )


def _build_cli_env(config: TutrConfig, tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["TUTR_UPDATE_CHECK"] = "0"

    if not _has_integration_overrides():
        return env

    home = tmp_path / "home"
    config_dir = home / ".tutr"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(
        json.dumps(config.model_dump(exclude_none=True), indent=2),
        encoding="utf-8",
    )
    env["HOME"] = str(home)
    return env


def _run_tutr_cli(
    words: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tutr-cli", *words],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )


def _run_tutr_cli_with_retries(
    words: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    raw_attempts = os.environ.get("TUTR_INTEGRATION_RETRIES", "2")
    raw_backoff = os.environ.get("TUTR_INTEGRATION_RETRY_BACKOFF_SECONDS", "2")
    try:
        attempts = max(1, int(raw_attempts))
    except ValueError:
        raise AssertionError(
            f"Invalid TUTR_INTEGRATION_RETRIES value: {raw_attempts!r}; expected integer."
        ) from None
    try:
        backoff_seconds = max(0.0, float(raw_backoff))
    except ValueError:
        raise AssertionError(
            "Invalid TUTR_INTEGRATION_RETRY_BACKOFF_SECONDS value: "
            f"{raw_backoff!r}; expected number."
        ) from None

    latest: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        latest = _run_tutr_cli(words, cwd=cwd, env=env)
        if latest.returncode == 0 and "$ " in latest.stdout:
            return latest
        if attempt < attempts and backoff_seconds > 0:
            time.sleep(backoff_seconds)
    assert latest is not None
    return latest


def _wait_between_live_requests() -> None:
    raw_wait = os.environ.get("TUTR_INTEGRATION_WAIT_SECONDS", "0")
    try:
        wait_seconds = float(raw_wait)
    except ValueError:
        raise AssertionError(
            f"Invalid TUTR_INTEGRATION_WAIT_SECONDS value: {raw_wait!r}; expected number."
        ) from None
    if wait_seconds <= 0:
        return

    global _LAST_LIVE_CALL_AT
    now = time.monotonic()
    if _LAST_LIVE_CALL_AT is not None:
        elapsed = now - _LAST_LIVE_CALL_AT
        remaining = wait_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
    _LAST_LIVE_CALL_AT = time.monotonic()


class CommandExpectationVariant(BaseModel):
    command_any_of: list[str]
    required_short_flags: list[str] = []
    required_long_flags: list[str] = []
    required_tokens: list[str] = []
    required_substrings: list[str] = []
    command_position: Literal["any", "first"] = "any"


class CliOutputCase(BaseModel):
    input: str
    expected_any_of: list[CommandExpectationVariant]
    quality_hint: str


def _load_case(raw: CliOutputCase, idx: int) -> CliOutputCase:
    if not raw.input.strip():
        raise AssertionError(f"Case #{idx} has empty 'input'.")
    if not raw.expected_any_of:
        raise AssertionError(f"Case #{idx} must define at least one expectation variant.")
    if not raw.quality_hint.strip():
        raise AssertionError(f"Case #{idx} must define non-empty 'quality_hint'.")
    return raw


def _load_cases() -> list[CliOutputCase]:
    if not _CASES_FILE.exists():
        raise AssertionError(f"Missing integration case file: {_CASES_FILE}")

    raw = json.loads(_CASES_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise AssertionError(f"{_CASES_FILE} must contain a JSON array of case objects.")
    if not raw:
        raise AssertionError(f"{_CASES_FILE} must contain at least one case.")

    cases: list[CliOutputCase] = []
    for idx, item in enumerate(raw, start=1):
        try:
            parsed = CliOutputCase.model_validate(item)
        except ValidationError as exc:
            raise AssertionError(f"Invalid case #{idx} in {_CASES_FILE}: {exc}") from None
        cases.append(_load_case(parsed, idx=idx))
    return cases


CASES = _load_cases()


def _split_pipeline_segments(command: str) -> list[list[str]]:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise AssertionError(f"failed to parse command tokens: {command!r} ({exc})") from None
    if not tokens:
        raise AssertionError("expected non-empty command")

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token == "|":
            if not current:
                raise AssertionError(f"invalid pipeline syntax in command: {command!r}")
            segments.append(current)
            current = []
            continue
        current.append(token)
    if not current:
        raise AssertionError(f"invalid pipeline syntax in command: {command!r}")
    segments.append(current)
    return segments


def _normalized_short_flags(tokens: list[str]) -> set[str]:
    chars: set[str] = set()
    for token in tokens:
        if token.startswith("--") or not token.startswith("-") or token == "-":
            continue
        for ch in token[1:]:
            chars.add(ch)
    return chars


def _normalized_long_flags(tokens: list[str]) -> set[str]:
    flags: set[str] = set()
    for token in tokens:
        if not token.startswith("--"):
            continue
        flag = token[2:].split("=", 1)[0].strip()
        if flag:
            flags.add(flag)
    return flags


def _matches_variant(command: str, variant: CommandExpectationVariant) -> bool:
    segments = _split_pipeline_segments(command)
    command_names = [segment[0] for segment in segments if segment]
    lower_command = command.lower()
    lower_tokens = {token.lower() for segment in segments for token in segment}
    expected_commands = {name.lower() for name in variant.command_any_of}

    matching_segment_indexes = [
        idx for idx, name in enumerate(command_names) if name.lower() in expected_commands
    ]
    if variant.command_position == "first":
        matching_segment_indexes = [idx for idx in matching_segment_indexes if idx == 0]
    if not matching_segment_indexes:
        return False

    for token in variant.required_tokens:
        if token.lower() not in lower_tokens:
            return False
    for snippet in variant.required_substrings:
        if snippet.lower() not in lower_command:
            return False

    segment = segments[matching_segment_indexes[0]]
    short_flags = _normalized_short_flags(segment[1:])
    long_flags = _normalized_long_flags(segment[1:])
    for flag in variant.required_short_flags:
        if flag not in short_flags:
            return False
    for flag in variant.required_long_flags:
        if flag not in long_flags:
            return False
    return True


def test_matcher_allows_print_for_literal_output_case() -> None:
    variant = CommandExpectationVariant(
        command_any_of=["echo", "printf", "print"],
        required_substrings=["INTEGRATION_OK"],
        command_position="first",
    )
    assert _matches_variant("print INTEGRATION_OK", variant)


def test_matcher_rejects_non_cwd_print_for_cwd_case() -> None:
    variant = CommandExpectationVariant(
        command_any_of=["echo", "printf", "print"],
        required_substrings=["PWD"],
        command_position="first",
    )
    assert not _matches_variant("print *", variant)


class TestCliOutputEvaluation:
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "case",
        CASES,
    )
    def test_tutr_cli_compiles_expected_outputs(self, case: CliOutputCase, tmp_path: Path) -> None:
        config = _load_live_config()
        env = _build_cli_env(config, tmp_path)
        _wait_between_live_requests()

        completed = _run_tutr_cli_with_retries(case.input.split(), cwd=tmp_path, env=env)
        cli_output = f"{completed.stdout}\n{completed.stderr}".strip()
        assert completed.returncode == 0, (
            f"tutr-cli failed for input {case.input!r}\n"
            f"exit={completed.returncode}\noutput:\n{cli_output}"
        )

        assert "$ " in completed.stdout, (
            f"unexpected CLI output for input {case.input!r}; "
            f"missing command prompt line in stdout:\n{completed.stdout}"
        )

        command = _extract_suggested_command(completed.stdout)
        _assert_safe_single_command(command)

        # Accuracy: command should semantically match one accepted structured variant.
        assert any(_matches_variant(command, variant) for variant in case.expected_any_of), (
            f"low-accuracy command: {command!r}; expected pattern hint: {case.quality_hint}"
        )

        # Quality: concise, direct command without shell chaining.
        assert len(command) <= 120, f"command is too verbose: {command!r}"
        assert "&&" not in command and ";" not in command, (
            f"expected one direct command, got: {command!r}"
        )
