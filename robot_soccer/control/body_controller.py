import threading
from typing import Optional

from robot_soccer.config import Config
from robot_soccer.ros.ros2_bridge import Ros2Bridge
from robot_soccer.state import SharedState
from robot_soccer.timing import Rate


class BodyController:
    def __init__(self, config: Config, ros2_bridge: Ros2Bridge, shared_state: SharedState) -> None:
        self._config = config
        self._ros2_bridge = ros2_bridge
        self._shared_state = shared_state
        self._rate = Rate(self._config.body.rate)
        self._thread: Optional[threading.Thread] = None

    def _clamp(self, value: float, min: float, max: float) -> float:
        if value > max:
            return max
        if value < min:
            return min
        return value

    def move(
        self,
        surge: float = 0.0,
        sway: float = 0.0,
        yaw: float = 0.0,
        duration: float = 1.0,
    ) -> None:
        self._ros2_bridge.publish_body_command(surge=surge, sway=sway, yaw=yaw, duration=duration)

    def hold(self):
        self.move(surge=0.0, sway=0.0, yaw=0.0, duration=1)
