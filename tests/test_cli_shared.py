"""Unit tests for tutr.cli.shared."""

from unittest.mock import patch

from tutr.cli.shared import format_suggested_command, supports_color
from tutr.constants import BOLD, CYAN, RESET


class TestSupportsColor:
    def test_returns_false_when_no_color_set(self) -> None:
        with patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "xterm-256color"}, clear=True):
            with patch("tutr.cli.shared.sys.stdout.isatty", return_value=True):
                assert supports_color() is False

    def test_returns_false_when_term_is_dumb(self) -> None:
        with patch.dict("os.environ", {"TERM": "dumb"}, clear=True):
            with patch("tutr.cli.shared.sys.stdout.isatty", return_value=True):
                assert supports_color() is False

    def test_returns_false_when_stdout_is_not_tty(self) -> None:
        with patch.dict("os.environ", {"TERM": "xterm-256color"}, clear=True):
            with patch("tutr.cli.shared.sys.stdout.isatty", return_value=False):
                assert supports_color() is False

    def test_returns_true_when_tty_and_color_allowed(self) -> None:
        with patch.dict("os.environ", {"TERM": "xterm-256color"}, clear=True):
            with patch("tutr.cli.shared.sys.stdout.isatty", return_value=True):
                assert supports_color() is True


class TestFormatSuggestedCommand:
    def test_uses_color_when_supported(self) -> None:
        with patch("tutr.cli.shared.supports_color", return_value=True):
            assert format_suggested_command("ls -la") == f"{BOLD}{CYAN}$ ls -la{RESET}"

    def test_falls_back_to_plain_text_when_color_unsupported(self) -> None:
        with patch("tutr.cli.shared.supports_color", return_value=False):
            assert format_suggested_command("ls -la") == "$ ls -la"
