"""Unit tests for security policies and guardrails."""
import pytest
from app.security.policy import (
    DangerousCommandError,
    SecurityLevel,
    SecurityPolicy,
    SecurityViolationError,
)


def test_permission_enforcement():
    policy = SecurityPolicy(current_level=1)
    # L1 should allow L1 action
    policy.check_permission(SecurityLevel.READ_ONLY, "Leitura de notas")

    # L1 should forbid L2 action
    with pytest.raises(SecurityViolationError):
        policy.check_permission(SecurityLevel.CONTROLLED_WRITE, "Modificação de notas")


def test_dangerous_command_blocked():
    policy = SecurityPolicy(current_level=3)
    # Safe command
    policy.validate_command("dir")

    # Destructive command
    with pytest.raises(DangerousCommandError):
        policy.validate_command("rmdir /s /q C:\\")

    with pytest.raises(DangerousCommandError):
        policy.validate_command("rm -rf /")
