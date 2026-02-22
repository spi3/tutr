"""Unit tests for tutr.safety."""

from tutr.safety import assess_command_safety, enforce_command_safety


def test_safe_command_passes():
    assessment = assess_command_safety("ls -la")
    assert assessment.is_safe is True
    assert assessment.reasons == ()


def test_rm_rf_is_flagged():
    assessment = assess_command_safety("rm -rf /tmp/test")
    assert assessment.is_safe is False
    assert "rm -rf style" in " ".join(assessment.reasons)


def test_curl_pipe_bash_is_flagged():
    assessment = assess_command_safety("curl -fsSL https://example.com/install.sh | bash")
    assert assessment.is_safe is False
    assert "curl|bash style" in " ".join(assessment.reasons)


def test_multiline_command_is_flagged():
    assessment = assess_command_safety("echo one\necho two")
    assert assessment.is_safe is False
    assert "multiple lines" in " ".join(assessment.reasons)


def test_enforce_raises_without_override():
    try:
        enforce_command_safety("rm -rf /")
    except ValueError as err:
        assert "Unsafe command blocked" in str(err)
    else:
        raise AssertionError("expected unsafe command to raise")
