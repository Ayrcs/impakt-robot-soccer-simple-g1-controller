import threading
import time
from typing import Optional, Tuple

from config import Config
from ros2_bridge import Ros2Bridge
from shared_state import SharedState
from timing import Rate


class HeadServosController:
    def __init__(self, shared_state: SharedState, ros2_bridge: Ros2Bridge, config: Config) -> None:
        self._shared_state: SharedState = shared_state
        self._ros2_bridge: Ros2Bridge = ros2_bridge
        self._config = config
        self._rate = Rate(self._config.servos.rate)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        pass

    def _run(self) -> None:
        while self._shared_state.is_running:
            yaw, pitch = self._compute_target_angles() # calculate new angles
            self.look_at(yaw=yaw, pitch=pitch) # publish new angles
            self._rate.sleep() # wait for the desired rate

    def _compute_target_angles(self) -> Tuple[float, float]:
        ball = self._shared_state.get_ball()
        head = self._shared_state._head

        error_x = self._config.camera.width / 2.0 - ball.x
        error_y = self._config.camera.height / 2.0 - ball.y

        yaw = self._apply_p_control(current=head.yaw, error=error_x)
        pitch = self._apply_p_control(current=head.pitch, error=error_y)
        return yaw, pitch

    def _apply_p_control(self, current: float, error: float) -> float:
        if abs(error) <= self._config.servos.dead_zone_px:
            return current

        return current + self._config.servos.kp * error

    def look_at(self, yaw: float, pitch: float) -> None:
        yaw = self._clamp(value=yaw, limit=self._config.servos.max_yaw)
        pitch = self._clamp(value=pitch, limit=self._config.servos.max_pitch)

        self._ros2_bridge.publish_head_command(yaw=yaw, pitch=pitch)

    @staticmethod
    def _clamp(value: float, limit: float) -> float:
        if value > limit:
            return limit
        if value < -limit:
            return -limit
        return value
