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

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.hold()

    def _run(self) -> None:
        kp = 2 / (self._config.camera.width + self._config.servos.max_yaw) * 3

        self._wait_for_ball()

        while self._shared_state.is_running:
            ball = self._shared_state.get_ball()
            head = self._shared_state.get_head()

            yaw = (ball.error_x + head.yaw) * kp
            print(f"Ask body position {yaw}")
            if abs(yaw) > 0.3:
                self.move(yaw=round(yaw, 2), duration=1)

            self._rate.sleep()

    def _clamp(self, value: float, min: float, max: float) -> float:
        if value > max:
            return max
        if value < min:
            return min
        return value

    def _wait_for_ball(self):
        print("Waiting for ball...")
        while True:
            ball = self._shared_state.get_ball()
            if ball.x is not None and ball.y is not None:
                break
            self._rate.sleep()
        print("Ball detected for the first time")

    def move(
        self,
        surge: float = 0.0,
        sway: float = 0.0,
        yaw: float = 0.0,
        duration: float = 0.0,
    ) -> None:
        self._ros2_bridge.publish_body_command(surge=surge, sway=sway, yaw=yaw, duration=duration)

    def hold(self):
        self.move(surge=0.0, sway=0.0, yaw=0.0, duration=1)
