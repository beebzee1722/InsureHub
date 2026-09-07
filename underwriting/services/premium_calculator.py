"""Premium calculation service for insurance underwriting."""

from decimal import ROUND_HALF_UP, Decimal


def calculate_premium(risk_score, coverage_limit):
    """Calculate premium based on risk score and coverage limit.

    Formula: risk_score * 12 * (coverage_limit / 1000)

    Args:
        risk_score: Risk score between 0-100 (float or Decimal)
        coverage_limit: Coverage limit in £ (Decimal)

    Returns:
        Decimal: Premium rounded to 2 decimal places

    Raises:
        TypeError: If inputs are None
        ValueError: If risk_score not in 0-100 or coverage_limit <= 0
    """
    if risk_score is None or coverage_limit is None:
        raise TypeError("risk_score and coverage_limit cannot be None")

    # Convert to Decimal for financial calculations
    risk_score = Decimal(str(risk_score))
    coverage_limit = Decimal(str(coverage_limit))

    # Validate risk_score range
    if risk_score < 0 or risk_score > 100:
        raise ValueError(f"risk_score must be between 0 and 100, got {risk_score}")

    # Validate coverage_limit
    if coverage_limit <= 0:
        raise ValueError(f"coverage_limit must be greater than 0, got {coverage_limit}")

    # Calculate premium: risk_score * 12 * (coverage_limit / 1000)
    premium = risk_score * Decimal(12) * (coverage_limit / Decimal(1000))

    # Round to 2 decimal places using ROUND_HALF_UP
    return premium.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_premium_with_overrides(base_premium, deductible, risk_override_pct):
    """Calculate adjusted premium with deductible and risk override.

    Formula:
        deductible_factor = 1.0 - (deductible - 250) / 1750 * 0.15
        override_factor = 1.0 + (risk_pct / 100)
        result = base * deductible_factor * override_factor

    Args:
        base_premium: Base premium (Decimal)
        deductible: Deductible in £ (250-2000)
        risk_override_pct: Risk override percentage (-25 to +25)

    Returns:
        Decimal: Adjusted premium rounded to 2 decimal places

    Raises:
        TypeError: If inputs are None
        ValueError: If deductible not in 250-2000 or risk_override_pct not in -25 to +25
    """
    if base_premium is None or deductible is None or risk_override_pct is None:
        raise TypeError(
            "base_premium, deductible, and risk_override_pct cannot be None"
        )

    # Convert to Decimal for financial calculations
    base_premium = Decimal(str(base_premium))
    deductible = Decimal(str(deductible))
    risk_override_pct = Decimal(str(risk_override_pct))

    # Validate deductible range
    if deductible < 250 or deductible > 2000:
        raise ValueError(f"deductible must be between 250 and 2000, got {deductible}")

    # Validate risk_override_pct range
    if risk_override_pct < -25 or risk_override_pct > 25:
        raise ValueError(
            f"risk_override_pct must be between -25 and 25, got {risk_override_pct}"
        )

    # Calculate deductible_factor: 1.0 - (deductible - 250) / 1750 * 0.15
    deductible_factor = Decimal("1.0") - (deductible - Decimal(250)) / Decimal(
        1750
    ) * Decimal("0.15")

    # Calculate override_factor: 1.0 + (risk_pct / 100)
    override_factor = Decimal("1.0") + (risk_override_pct / Decimal(100))

    # Calculate adjusted premium: base * deductible_factor * override_factor
    adjusted_premium = base_premium * deductible_factor * override_factor

    # Round to 2 decimal places using ROUND_HALF_UP
    return adjusted_premium.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
