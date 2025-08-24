#!/usr/bin/env python3
"""Simulate API authentication flows.

Usage:
    uv run scripts/api_auth_simulation.py --token <TOKEN>
"""

import argparse
import secrets

EXPECTED_TOKEN = "secret-token"


def authenticate(token: str | None) -> tuple[int, str]:
    """Verify the provided token.

    Args:
        token: Token from the request.

    Returns:
        Tuple of status code and message describing result.
    """
    if not token:
        return 400, "missing credential"
    if secrets.compare_digest(token, EXPECTED_TOKEN):
        return 200, "authorized"
    return 401, "unauthorized"


def main() -> None:
    """Parse arguments and run the simulation."""
    parser = argparse.ArgumentParser(description="Simulate API authentication")
    parser.add_argument("--token", help="token to validate")
    args = parser.parse_args()
    code, msg = authenticate(args.token)
    print(f"{code}: {msg}")


if __name__ == "__main__":
    main()
