"""Simulate credential checks for API auth.

Usage:
    uv run scripts/api_auth_credentials_sim.py
"""

from __future__ import annotations

from secrets import compare_digest

EXPECTED_TOKEN = "secret-token"
PERMISSIONS = {"admin": {"read", "write"}, "reader": {"read"}}


def authenticate(token: str, role: str, action: str) -> bool:
    """Return True when the token and role authorize the action."""
    return compare_digest(token, EXPECTED_TOKEN) and action in PERMISSIONS.get(role, set())


def main() -> None:  # pragma: no cover - CLI usage
    scenarios = [
        ("secret-token", "admin", "write"),
        ("bad-token", "admin", "write"),
        ("secret-token", "reader", "write"),
    ]
    for tok, role, action in scenarios:
        allowed = authenticate(tok, role, action)
        status = "allowed" if allowed else "denied"
        print(f"{role} using {tok!r} for {action}: {status}")


if __name__ == "__main__":
    main()
