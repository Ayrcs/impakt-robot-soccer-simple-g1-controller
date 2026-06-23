import signal
import time

import ros2_bridge
from config import Config
from head_servos_controller import HeadServosController
from ros2_bridge import Ros2Bridge
from shared_state import SharedState
from vision_bridge import VisionBridge


class Robot:
    def __init__(self):
        self._config = Config()
        self.shared_state = SharedState()

        # Acquisition
        self._vision_bridge = VisionBridge(shared_state=self.shared_state, config=self._config)
        self._ros2_bridge = Ros2Bridge(config=self._config, shared_state=self.shared_state)

        # Controller
        self._head_servos_controller: HeadServosController = HeadServosController(shared_state=self.shared_state, ros2_bridge=self._ros2_bridge, config=self._config)

        self._stopped = False

    def start(self) -> None:
        if self._config.ros2.enabled: self._ros2_bridge.start()
        if self._config.detector.enabled: self._vision_bridge.start()
        if self._config.servos.enabled: self._head_servos_controller.start()

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        self.shared_state.is_running = False
        self._ros2_bridge.stop()
        self._vision_bridge.stop()
        self._head_servos_controller.stop()


def _request_stop(robot: Robot) -> None:
    print("Stopping robot")
    robot.stop()


if __name__ == "__main__":
    robot = Robot()
    signal.signal(signal.SIGTERM, lambda signum, frame: _request_stop(robot))
    robot.start()

    try:
        while robot.shared_state.is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        _request_stop(robot)
    finally:
        robot.stop()
