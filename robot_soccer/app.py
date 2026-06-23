from robot_soccer.config import Config
from robot_soccer.control.body_controller import BodyController
from robot_soccer.control.head_controller import HeadController
from robot_soccer.ros.ros2_bridge import Ros2Bridge
from robot_soccer.state import SharedState
from robot_soccer.vision.vision_worker import VisionWorker


class RobotApp:
    def __init__(self) -> None:
        self._config = Config()
        self.shared_state = SharedState()

        self._vision_worker = VisionWorker(
            shared_state=self.shared_state,
            config=self._config
        )
        self._ros2_bridge = Ros2Bridge(
            config=self._config,
            shared_state=self.shared_state
        )

        self._head_controller = HeadController(
            shared_state=self.shared_state,
            ros2_bridge=self._ros2_bridge,
            config=self._config,
        )
        self._body_controller = BodyController(
            shared_state=self.shared_state,
            ros2_bridge=self._ros2_bridge,
            config=self._config,
        )

        self._stopped = False

    def start(self) -> None:
        if self._config.ros2.enabled:
            self._ros2_bridge.start()
        if self._config.servos.enabled:
            self._head_controller.start()
        if self._config.body.enabled:
            self._body_controller.start()
        if self._config.detector.enabled:
            self._vision_worker.start()

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        self.shared_state.is_running = False
        self._body_controller.stop()
        self._vision_worker.stop()
        self._head_controller.stop()
        self._ros2_bridge.stop()
