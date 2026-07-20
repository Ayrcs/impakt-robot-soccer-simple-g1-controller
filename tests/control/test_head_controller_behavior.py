import sys
import types
from types import SimpleNamespace

from robot_soccer.state import Ball
from robot_soccer.state import Head


ros2_bridge_module = types.ModuleType("robot_soccer.ros.ros2_bridge")


class Ros2Bridge:
    pass


ros2_bridge_module.Ros2Bridge = Ros2Bridge
sys.modules.setdefault("robot_soccer.ros.ros2_bridge", ros2_bridge_module)

from robot_soccer.control.head_controller import HeadController


class FakeSharedState:
    def __init__(self, ball=None, head=None):
        self._ball = ball or Ball()
        self._head = head or Head()
        self.is_running = True

    def get_ball(self):
        return self._ball

    def get_head(self):
        return self._head

    def is_ball_seen_now(self):
        return self._ball.seen

    def is_ball_seen_recently(self):
        return self._ball.seen


class FakeRos2Bridge:
    def __init__(self):
        self.head_commands = []

    def publish_head_command(self, yaw, pitch):
        self.head_commands.append((yaw, pitch))


def make_config():
    return SimpleNamespace(
        servos=SimpleNamespace(
            rate=10,
            dead_zone_px=10,
            kp=0.1,
            max_yaw=45,
            min_pitch=-20,
            max_pitch=80,
        ),
    )


def test_apply_p_control_keeps_current_value_inside_dead_zone():
    controller = HeadController(
        shared_state=FakeSharedState(),
        ros2_bridge=FakeRos2Bridge(),
        config=make_config(),
    )

    assert controller._apply_p_control(current=12.0, error=10.0) == 12.0
    assert controller._apply_p_control(current=12.0, error=None) == 12.0


def test_apply_p_control_defaults_missing_current_to_zero():
    controller = HeadController(
        shared_state=FakeSharedState(),
        ros2_bridge=FakeRos2Bridge(),
        config=make_config(),
    )

    assert controller._apply_p_control(current=None, error=20.0) == 2.0


def test_stare_ball_publishes_proportional_head_command():
    shared_state = FakeSharedState(
        ball=Ball(error_x=20.0, error_y=-30.0),
        head=Head(yaw=5.0, pitch=10.0),
    )
    bridge = FakeRos2Bridge()
    controller = HeadController(
        shared_state=shared_state,
        ros2_bridge=bridge,
        config=make_config(),
    )

    controller.stare_ball()

    assert bridge.head_commands == [(7.0, 7.0)]


def test_look_at_clamps_angles_before_publishing():
    bridge = FakeRos2Bridge()
    controller = HeadController(
        shared_state=FakeSharedState(),
        ros2_bridge=bridge,
        config=make_config(),
    )

    controller.look_at(yaw=90.0, pitch=-90.0)

    assert bridge.head_commands == [(45, -20)]
