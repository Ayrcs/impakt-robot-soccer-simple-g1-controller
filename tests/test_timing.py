import pytest
import robot_soccer.timing as timing_module
from robot_soccer.timing import Rate
from robot_soccer.timing import is_fresh


def test_rate_creation():
    rate = Rate(10)
    assert rate is not None


def test_rate_rejects_non_positive_frequency():
    with pytest.raises(ValueError, match="Rate must be positive"):
        Rate(0)


def test_rate_sleep_waits_remaining_period(monkeypatch):
    monotonic_values = iter([100.0, 100.03])
    sleep_calls = []

    monkeypatch.setattr(timing_module.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(timing_module.time, "sleep", sleep_calls.append)

    rate = Rate(10)

    assert rate.sleep() is True
    assert sleep_calls == [pytest.approx(0.07)]


def test_rate_sleep_skips_sleep_when_late(monkeypatch):
    monotonic_values = iter([100.0, 100.2])
    sleep_calls = []

    monkeypatch.setattr(timing_module.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(timing_module.time, "sleep", sleep_calls.append)

    rate = Rate(10)

    assert rate.sleep() is True
    assert sleep_calls == []


def test_is_fresh_rejects_empty_timestamp():
    assert is_fresh(timestamp=0.0, max_age=2.0) is False


def test_is_fresh_uses_monotonic_age(monkeypatch):
    monkeypatch.setattr(timing_module.time, "monotonic", lambda: 12.0)

    assert is_fresh(timestamp=10.5, max_age=2.0) is True
    assert is_fresh(timestamp=9.5, max_age=2.0) is False
