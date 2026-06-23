import json
import threading
import time
from typing import Optional

import cv2
import rclpy
from rclpy.executors import ExternalShutdownException, ShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from unitree_go.msg import MotorStates, MotorCmd, MotorCmds
from unitree_api.msg import Request, RequestHeader, RequestIdentity, RequestLease, RequestPolicy

import numpy as np

from robot_soccer.config import Config
from robot_soccer.state import Head, SharedState


class Ros2Bridge(Node):
    def __init__(self, config: Config, shared_state: SharedState) -> None:
        if not rclpy.ok():
            rclpy.init()

        super().__init__("ros2_bridge")
        self._config: Config = config
        self._shared_state: SharedState = shared_state
        self._spin_thread: Optional[threading.Thread] = None
        self._stopped = False

        # Subscription for camera images
        self._image_subscription = self.create_subscription(
            CompressedImage,
            self._config.ros2.camera_topic,
            self._on_compressed_image,
            10,
        )
        # Subscription for camera compression joints (servos)
        self._head_servos_state_subscription = self.create_subscription(
            MotorStates,
            config.ros2.head_servos_state_topic,
            self._on_head_servos_state,
            10,
        )

        # Publisher for camera compression joints (servos)
        self._head_servos_command_publisher = self.create_publisher(
            MotorCmds,
            config.ros2.head_servos_command_topic,
            10,
        )

        # Publisher for high control body movements
        self._body_high_level_command_publisher = self.create_publisher(
            Request,
            config.ros2.high_level_body_movements_topic,
            10,
        )

    def start(self) -> None:
        if self._spin_thread is not None and self._spin_thread.is_alive():
            return

        self._spin_thread = threading.Thread(target=self._spin, daemon=True)
        print("Starting ros2_bridge")
        self._spin_thread.start()


    def stop(self) -> None:
        if self._stopped:
            return

        self._stopped = True
        if rclpy.ok():
            rclpy.shutdown()

        if self._spin_thread is not None and self._spin_thread.is_alive():
            self._spin_thread.join(timeout=2)

        self.destroy_node()
        print("Stopping ros2_bridge")

    def _spin(self) -> None:
        try:
            rclpy.spin(self)
        except (ExternalShutdownException, ShutdownException):
            pass

    def _on_compressed_image(self, msg: CompressedImage) -> None:
        image = self._decode_compressed_image(msg, cv2.IMREAD_COLOR)
        if image is None:
            return
        self._shared_state.set_image(image=image, timestamp=time.time())

    def _decode_compressed_image(self, msg: CompressedImage, flags: int) -> Optional[np.ndarray]:
        encoded = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, flags)
        if frame is None:
            print("Unable to decode compressed image")
        return frame

    def _on_head_servos_state(self, msg: MotorStates) -> None:
        # print(f"Received MotorStates={msg}")
        self._shared_state.set_head(head=Head(
            mode=msg.states[0].mode,
            yaw=msg.states[0].q,
            pitch=msg.states[1].q,
            timestamp = time.time()
        ))

    def publish_head_command(self, yaw: float, pitch: float) -> None:
        message: MotorCmds = self._build_head_command_payload(mode=1, yaw=yaw, pitch=pitch)
        self._head_servos_command_publisher.publish(message)
        # print(f"Published head message={message}")

    def publish_body_command(self, surge: float = 0.0, sway: float = 0.0, yaw: float = 0.0, duration: float = 0.0) -> None:
        message: Request = self._build_body_command_payload(surge=surge, sway=sway, yaw=yaw, duration=duration)
        self._body_high_level_command_publisher.publish(message)
        print(f"Published head message={message}")

    def _build_head_command_payload(self, mode: int, yaw: float, pitch: float) -> MotorCmds:
        return MotorCmds(
            cmds=[
                MotorCmd(mode=mode, q=float(yaw)),
                MotorCmd(mode=mode, q=float(pitch))
            ]
        )

    def _build_body_command_payload(self, surge: float = 0.0, sway: float = 0.0, yaw: float = 0.0,
                                    duration: float = 0.0) -> Request:
        return Request(
            header=RequestHeader(
                identity=RequestIdentity(
                    id=0,
                    api_id=7105,
                ),
                lease=RequestLease(
                    id=0,
                ),
                policy=RequestPolicy(
                    priority=0,
                    noreply=False,
                ),
            ),
            parameter=json.dumps({
                "velocity": [float(surge), float(sway), float(yaw)],
                "duration": float(duration),
            }),
            binary=[],
        )
