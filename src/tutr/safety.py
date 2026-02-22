"""Safety checks for model-suggested shell commands."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSafetyAssessment:
    """Result of evaluating whether a suggested command looks dangerous."""

    is_safe: bool
    reasons: tuple[str, ...]


class UnsafeCommandError(ValueError):
    """Raised when a command is blocked by the safety filter."""

    def __init__(self, reasons: tuple[str, ...]):
        reason_text = "; ".join(reasons)
        super().__init__(f"Unsafe command blocked: {reason_text}")
        self.reasons = reasons


_DANGEROUS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\brm\s+-[^\n]*(?:r[^\n]*f|f[^\n]*r)\b", re.IGNORECASE),
        "contains recursive force delete (rm -rf style)",
    ),
    (
        re.compile(r"\bmkfs(?:\.[a-z0-9_+-]+)?\b", re.IGNORECASE),
        "contains filesystem formatting command (mkfs)",
    ),
    (
        re.compile(r"\bdd\b", re.IGNORECASE),
        "contains raw disk copy command (dd)",
    ),
    (
        re.compile(r"\b(?:shutdown|reboot|halt|poweroff|killall)\b", re.IGNORECASE),
        "contains system/process shutdown command",
    ),
    (
        re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:bash|sh|zsh|ksh|fish)\b", re.IGNORECASE),
        "contains pipe-to-shell execution (curl|bash style)",
    ),
    (
        re.compile(r":\s*\(\s*\)\s*{[^}]*:\s*\|:\s*;[^}]*}\s*;?\s*:", re.IGNORECASE),
        "contains fork bomb pattern",
    ),
    (
        re.compile(r"`[^`\n]+`|\$\([^)\n]+\)"),
        "contains command substitution",
    ),
)


def is_unsafe_override_enabled() -> bool:
    """Return whether unsafe-command override is enabled by environment."""
    return os.getenv("TUTR_ALLOW_UNSAFE", "").strip().lower() in {"1", "true", "yes", "on"}


def assess_command_safety(command: str) -> CommandSafetyAssessment:
    """Assess whether a command should be treated as unsafe."""
    reasons: list[str] = []
    if "\n" in command or "\r" in command:
        reasons.append("contains multiple lines")
    for pattern, reason in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            reasons.append(reason)
    return CommandSafetyAssessment(is_safe=not reasons, reasons=tuple(reasons))


def enforce_command_safety(command: str, *, allow_unsafe: bool = False) -> CommandSafetyAssessment:
    """Validate command safety and optionally block unsafe commands."""
    assessment = assess_command_safety(command)
    if not assessment.is_safe and not allow_unsafe:
        raise UnsafeCommandError(assessment.reasons)
    return assessment
