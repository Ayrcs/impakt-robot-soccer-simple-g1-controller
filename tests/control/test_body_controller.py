import sys
import types
from types import SimpleNamespace


ros2_bridge_module = types.ModuleType("robot_soccer.ros.ros2_bridge")


class Ros2Bridge:
    pass


ros2_bridge_module.Ros2Bridge = Ros2Bridge
sys.modules.setdefault("robot_soccer.ros.ros2_bridge", ros2_bridge_module)

from robot_soccer.control.body_controller import BodyController


class FakeRos2Bridge:
    def __init__(self):
        self.body_commands = []

    def publish_body_command(self, surge=0.0, sway=0.0, yaw=0.0, duration=0.0):
        self.body_commands.append(
            {
                "surge": surge,
                "sway": sway,
                "yaw": yaw,
                "duration": duration,
            },
        )


def make_config():
    return SimpleNamespace(
        body=SimpleNamespace(rate=10),
    )


def test_move_publishes_body_command_values():
    bridge = FakeRos2Bridge()
    controller = BodyController(
        config=make_config(),
        ros2_bridge=bridge,
        shared_state=object(),
    )

    controller.move(surge=0.8, sway=-0.2, yaw=0.5, duration=3.0)

    assert bridge.body_commands == [
        {
            "surge": 0.8,
            "sway": -0.2,
            "yaw": 0.5,
            "duration": 3.0,
        },
    ]


def test_hold_publishes_zero_velocity_for_one_second():
    bridge = FakeRos2Bridge()
    controller = BodyController(
        config=make_config(),
        ros2_bridge=bridge,
        shared_state=object(),
    )

    controller.hold()

    assert bridge.body_commands == [
        {
            "surge": 0.0,
            "sway": 0.0,
            "yaw": 0.0,
            "duration": 1,
        },
    ]
