"""
GRIDMIND AI - Smart Grid Decision Advisor

Provides transparent, rule-based risk assessments and
recommendations using existing grid forecast decisions.

This module does not replace the trained forecasting model
or independently verify real-time grid conditions.
"""


def generate_grid_advice(
    demand_kw: float,
    grid_mode: str,
    critical_alert: bool,
    timestamp: str,
) -> dict:
    """
    Generate a risk assessment and recommended action
    for one forecast hour.
    """

    # Convert and validate predicted demand.
    demand = float(demand_kw)

    if not 0 <= demand < float("inf"):
        raise ValueError(
            "Demand must be a finite, non-negative number."
        )

    # Extract the forecast hour from its timestamp.
    try:
        hour = int(timestamp[11:13])
    except (ValueError, TypeError, IndexError):
        raise ValueError(
            "Timestamp must contain an hour in HH format."
        )

    if not 0 <= hour <= 23:
        raise ValueError("Timestamp hour must be between 0 and 23.")

    # Identify the evening storage window.
    is_evening_window = 18 <= hour <= 22

    # --------------------------------------------------
    # RISK ASSESSMENT
    # --------------------------------------------------

    if critical_alert or demand >= 200:
        risk_level = "High"
        priority = "Urgent"

        risk_reason = (
            f"Predicted demand is {demand:.2f} kW, "
            "meeting or exceeding the configured "
            "200 kW critical threshold."
        )

        recommended_action = (
            "Review available generation and storage capacity. "
            "Verify the forecast and follow established "
            "grid-operator procedures."
        )

    elif demand > 160 or is_evening_window:
        risk_level = "Medium"
        priority = "Elevated"

        if is_evening_window and demand <= 160:
            risk_reason = (
                f"The forecast falls within the configured "
                f"evening storage window ({hour:02d}:00)."
            )
        else:
            risk_reason = (
                f"Predicted demand is {demand:.2f} kW, "
                "above the configured 160 kW storage threshold."
            )

        recommended_action = (
            "Review renewable availability and storage readiness. "
            "Monitor upcoming demand forecasts for changes."
        )

    else:
        risk_level = "Low"
        priority = "Normal"

        risk_reason = (
            f"Predicted demand is {demand:.2f} kW, "
            "at or below 160 kW and outside the evening window."
        )

        recommended_action = (
            "Continue routine monitoring and review the next "
            "forecast update."
        )

    # --------------------------------------------------
    # RETURN ADVISORY INFORMATION
    # --------------------------------------------------

    return {
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "recommended_action": recommended_action,
        "priority": priority,
        "assessment_type": "Rule-based forecast assessment",
        "thresholds_kw": {
            "storage": 160,
            "critical": 200,
        },
    }
