from math import inf

import pytest

from robot_soccer.utils import clamp


@pytest.mark.parametrize("value", [-15.0, -inf])
def test_clamp_minimum(value):
    result = clamp(
        value=value,
        min=-10.0,
        max=10.0,
    )

    assert result == -10.0


@pytest.mark.parametrize("value", [15.0, inf])
def test_clamp_maximum(value):
    result = clamp(
        value=value,
        min=-10.0,
        max=10.0,
    )

    assert result == 10.0


def test_clamp_value_inside_bounds():
    result = clamp(
        value=5.0,
        min=-10.0,
        max=10.0,
    )

    assert result == 5.0


def test_clamp_exact_minimum():
    result = clamp(
        value=-10.0,
        min=-10.0,
        max=10.0,
    )

    assert result == -10.0


def test_clamp_exact_maximum():
    result = clamp(
        value=10.0,
        min=-10.0,
        max=10.0,
    )

    assert result == 10.0
