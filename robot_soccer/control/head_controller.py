import threading
import time
from typing import Optional

import numpy as np

from robot_soccer.config import Config
from robot_soccer.ros.ros2_bridge import Ros2Bridge
from robot_soccer.state import SharedState
from robot_soccer.timing import Rate


class HeadController:
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
            if self._shared_state.is_ball_recently_seen():
                self._run_ball_follow()
            else:
                self._run_ball_research()

    def _run_ball_follow(self) -> None:
        yaw, pitch = self._compute_target_angles()
        self.look_at(yaw=yaw, pitch=pitch)
        self._rate.sleep()

    def _run_ball_research(self) -> None:
        t = 0.0
        dt = 0.05
        speed = 2  # radians/seconde

        while self._shared_state.is_running and not self._shared_state.is_ball_seen():
            pitch = 3 + 20 * np.cos(t)
            yaw = 0 + 45 * np.sin(t)

            self.look_at(yaw=yaw, pitch=pitch)

            t += speed * dt
            time.sleep(dt)

    def _compute_target_angles(self):
        ball = self._shared_state.get_ball()
        head = self._shared_state.get_head()

        yaw = self._apply_p_control(current=head.yaw, error=ball.error_x)
        pitch = self._apply_p_control(current=head.pitch, error=ball.error_y)
        return yaw, pitch

    def _apply_p_control(self, current: float, error: float) -> float:
        if error is None or abs(error) <= self._config.servos.dead_zone_px:
            return current

        return current + self._config.servos.kp * error

    def look_at(self, yaw: float, pitch: float) -> None:
        yaw = self._clamp(value=yaw, min=-self._config.servos.max_yaw, max=self._config.servos.max_yaw)
        pitch = self._clamp(value=pitch, min=self._config.servos.min_pitch, max=self._config.servos.max_pitch)
        self._ros2_bridge.publish_head_command(yaw=yaw, pitch=pitch)

    @staticmethod
    def _clamp(value: float, min: float, max: float) -> float:
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
