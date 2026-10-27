import pytest

from grid_controller import evaluate_grid_state


def test_demand_160_outside_evening_window():
    result = evaluate_grid_state(160, "2026-10-26 12:00:00")

    assert result["grid_mode"] == "Main Grid Mode"
    assert result["critical_alert"] is False


def test_demand_above_160_uses_storage():
    result = evaluate_grid_state(160.1, "2026-10-26 12:00:00")

    assert result["grid_mode"] == "Renewable Storage Mode"
    assert result["critical_alert"] is False


def test_demand_200_triggers_critical_alert():
    result = evaluate_grid_state(200, "2026-10-26 12:00:00")

    assert result["grid_mode"] == "Renewable Storage Mode"
    assert result["critical_alert"] is True
    assert result["alert_message"] == "Critical Overload Alert"


def test_demand_100_at_17_uses_main_grid():
    result = evaluate_grid_state(100, "2026-10-26 17:00:00")

    assert result["grid_mode"] == "Main Grid Mode"


@pytest.mark.parametrize("hour", [18, 19, 20, 21, 22])
def test_evening_window_uses_storage(hour):
    timestamp = f"2026-10-26 {hour:02d}:00:00"

    result = evaluate_grid_state(100, timestamp)

    assert result["grid_mode"] == "Renewable Storage Mode"


@pytest.mark.parametrize("hour", [0, 12, 17, 23])
def test_outside_evening_window_uses_main_grid_for_low_demand(hour):
    timestamp = f"2026-10-26 {hour:02d}:00:00"

    result = evaluate_grid_state(100, timestamp)

    assert result["grid_mode"] == "Main Grid Mode"


def test_high_demand_triggers_alert_outside_evening_window():
    result = evaluate_grid_state(210, "2026-10-26 12:00:00")

    assert result["grid_mode"] == "Renewable Storage Mode"
    assert result["critical_alert"] is True


def test_evening_storage_mode_applies_even_at_low_demand():
    result = evaluate_grid_state(100, "2026-10-26 19:00:00")

    assert result["grid_mode"] == "Renewable Storage Mode"
    assert result["critical_alert"] is False


def test_negative_demand_is_rejected():
    with pytest.raises(ValueError):
        evaluate_grid_state(-1, "2026-10-26 12:00:00")


def test_invalid_timestamp_is_rejected():
    with pytest.raises(ValueError):
        evaluate_grid_state(100, "not-a-valid-timestamp")
