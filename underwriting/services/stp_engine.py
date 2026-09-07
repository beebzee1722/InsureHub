"""STP (Straight-Through Processing) Engine Service for InsureHub.

This module provides automatic decision-making for insurance applications
based on risk scores.
"""


def categorize_status(risk_score: float) -> str:
    """Categorize an application status based on risk score.

    Args:
        risk_score: A float between 0 and 100 representing the risk level.

    Returns:
        str: One of three status values:
            - "approved": risk_score < 20
            - "flagged": 20 <= risk_score <= 85
            - "rejected": risk_score > 85

    Raises:
        TypeError: If risk_score is not a float or numeric type.
        ValueError: If risk_score is outside the 0-100 range.
    """
    # Type validation
    if not isinstance(risk_score, (int, float)):
        raise TypeError(f"risk_score must be a float, got {type(risk_score).__name__}")

    # Range validation
    if risk_score < 0 or risk_score > 100:
        raise ValueError(f"risk_score must be between 0 and 100, got {risk_score}")

    # Categorization logic
    if risk_score < 20:
        return "approved"
    elif risk_score > 85:
        return "rejected"
    else:
        return "flagged"
