from datetime import datetime
from typing import Any


def evaluate_grid_state(
    demand_kw: float,
    timestamp: str | datetime,
) -> dict[str, Any]:
    """
    Decide the grid mode and overload alert for one forecast hour.

    Rules:
    1. Demand > 160 kW OR hour is 18 through 22 inclusive:
       Renewable Storage Mode.
    2. Otherwise:
       Main Grid Mode.
    3. Demand >= 200 kW:
       Critical Overload Alert, independently of grid mode.
    """

    # Validate the demand value.
    if isinstance(demand_kw, bool) or not isinstance(
        demand_kw, (int, float)
    ):
        raise TypeError("demand_kw must be a number.")

    if demand_kw != demand_kw or demand_kw in (float("inf"), float("-inf")):
        raise ValueError("demand_kw must be a finite number.")

    if demand_kw < 0:
        raise ValueError("demand_kw cannot be negative.")

    # Convert the timestamp to a datetime object.
    if isinstance(timestamp, datetime):
        forecast_time = timestamp
    elif isinstance(timestamp, str):
        try:
            forecast_time = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError(
                "timestamp must use a valid ISO date/time format."
            ) from exc
    else:
        raise TypeError("timestamp must be a string or datetime.")

    hour = forecast_time.hour

    # Apply the grid transition rule.
    is_evening_window = 18 <= hour <= 22

    if demand_kw > 160 or is_evening_window:
        grid_mode = "Renewable Storage Mode"
    else:
        grid_mode = "Main Grid Mode"

    # Evaluate the critical alert independently.
    critical_alert = demand_kw >= 200

    if critical_alert:
        explanation = (
            f"Predicted demand is {demand_kw:.2f} kW, "
            "which meets or exceeds the 200 kW critical threshold."
        )
    elif is_evening_window and demand_kw <= 160:
        explanation = (
            f"It is {hour:02d}:00, within the 18:00–22:00 "
            "storage window."
        )
    elif demand_kw > 160:
        explanation = (
            f"Predicted demand is {demand_kw:.2f} kW, "
            "above the 160 kW storage threshold."
        )
    else:
        explanation = (
            f"Predicted demand is {demand_kw:.2f} kW, "
            "at or below 160 kW and outside the evening window."
        )

    return {
        "timestamp": forecast_time.isoformat(sep=" "),
        "hour": hour,
        "predicted_demand_kw": float(demand_kw),
        "grid_mode": grid_mode,
        "critical_alert": critical_alert,
        "alert_message": (
            "Critical Overload Alert" if critical_alert else None
        ),
        "explanation": explanation,
    }