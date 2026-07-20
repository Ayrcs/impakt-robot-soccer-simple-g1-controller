from types import SimpleNamespace

import numpy as np

import robot_soccer.state as state_module
from robot_soccer.behavior.states import Behavior
from robot_soccer.state import Ball
from robot_soccer.state import Head
from robot_soccer.state import SharedState


def make_config(ball_close_diameter=65):
    return SimpleNamespace(
        detector=SimpleNamespace(ball_close_diameter=ball_close_diameter),
    )


def test_shared_state_starts_running_and_booting():
    shared_state = SharedState(config=make_config())

    assert shared_state.is_running is True
    assert shared_state.get_behavior() == Behavior.BOOTING
    assert shared_state.is_ball_seen_now() is False


def test_shared_state_updates_behavior_ball_and_head():
    shared_state = SharedState(config=make_config())
    ball = Ball(seen=True, diameter=42)
    head = Head(yaw=12.0, pitch=-4.0)

    shared_state.set_behavior(Behavior.FOLLOW_BALL)
    shared_state.set_ball(ball)
    shared_state.set_head(head)

    assert shared_state.get_behavior() == Behavior.FOLLOW_BALL
    assert shared_state.get_ball() is ball
    assert shared_state.get_head() is head


def test_set_ball_unseen_only_changes_seen_flag():
    shared_state = SharedState(config=make_config())
    shared_state.set_ball(Ball(seen=True, diameter=42))

    shared_state.set_ball_unseen()

    assert shared_state.get_ball().seen is False
    assert shared_state.get_ball().diameter == 42


def test_set_image_stores_image_and_default_timestamp(monkeypatch):
    shared_state = SharedState(config=make_config())
    image = np.zeros((2, 2, 3), dtype=np.uint8)

    monkeypatch.setattr(state_module.time, "time", lambda: 123.4)

    shared_state.set_image(image=image)

    assert shared_state.get_image().raw is image
    assert shared_state.get_image().timestamp == 123.4


def test_set_image_ignores_none_image():
    shared_state = SharedState(config=make_config())

    shared_state.set_image(image=None, timestamp=123.4)

    assert shared_state.get_image().raw is None
    assert shared_state.get_image().timestamp is None


def test_ball_seen_recently_requires_timestamp(monkeypatch):
    shared_state = SharedState(config=make_config())
    monkeypatch.setattr(state_module.time, "time", lambda: 100.0)

    assert shared_state.is_ball_seen_recently() is False

    shared_state.set_ball(Ball(timestamp=98.1))
    assert shared_state.is_ball_seen_recently() is True

    shared_state.set_ball(Ball(timestamp=97.9))
    assert shared_state.is_ball_seen_recently() is False


def test_ball_close_requires_seen_ball_and_large_enough_diameter():
    shared_state = SharedState(config=make_config(ball_close_diameter=65))

    shared_state.set_ball(Ball(seen=False, diameter=100))
    assert shared_state.is_ball_close() is False

    shared_state.set_ball(Ball(seen=True, diameter=None))
    assert shared_state.is_ball_close() is False

    shared_state.set_ball(Ball(seen=True, diameter=54.9))
    assert shared_state.is_ball_close() is False

    shared_state.set_ball(Ball(seen=True, diameter=55.1))
    assert shared_state.is_ball_close() is True
