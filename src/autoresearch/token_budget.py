"""Token budget utilities."""

from decimal import ROUND_HALF_UP, Decimal


def round_with_margin(usage: float, margin: float) -> int:
    """Return ``usage * (1 + margin)`` rounded half up.

    Args:
        usage: Baseline token usage.
        margin: Additional fractional margin to apply.

    Returns:
        int: Rounded token budget.
    """
    scaled = Decimal(str(usage)) * (Decimal("1") + Decimal(str(margin)))
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))
