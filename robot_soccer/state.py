import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from robot_soccer.behavior.states import Behavior
from robot_soccer.config import Config


@dataclass()
class Head:
    mode: int = None
    yaw: float = None
    pitch: float = None
    timestamp: float = None


@dataclass()
class Ball:
    x: float = None
    y: float = None
    error_x: float = None
    error_y: float = None
    diameter: float = None
    distance: float = None
    timestamp: float = None
    confidence: float = None
    seen: bool = False


@dataclass()
class Goal:
    x: float = None
    y: float = None
    error_x: float = None
    error_y: float = None
    diameter: float = None
    distance: float = None
    timestamp: float = None
    confidence: float = None
    seen: bool = False


@dataclass()
class Image:
    raw: Optional[np.ndarray] = None
    timestamp: float = None


class SharedState:
    def __init__(self, config: Config) -> None:
        self._lock = threading.Lock()
        self._ball = Ball()
        self._head = Head()
        self._image = Image()
        self._config = config
        self._behavior: Behavior = Behavior.BOOTING
        self.is_running = True

    def get_behavior(self) -> Behavior:
        return self._behavior

    def set_behavior(self, behavior: Behavior) -> None:
        with self._lock:
            self._behavior = behavior

    def get_image(self) -> Image:
        return self._image

    def set_image(self, image: Optional[np.ndarray] = None, timestamp: Optional[float] = None) -> None:
        with self._lock:
            if image is not None:
                self._image.raw = image
                self._image.timestamp = timestamp if timestamp is not None else time.time()

    def save_image(self, image: Optional[Image] = None) -> None:
        if image is None:
            image = self._image
        cv2.imwrite("frames/last_image.jpg", image.raw)

    def set_ball(self, ball: Ball) -> None:
        self._ball: Ball = ball

    def set_head(self, head: Head) -> None:
        self._head: Head = head

    def get_ball(self) -> Ball:
        return self._ball

    def get_head(self) -> Head:
        return self._head

    def set_ball_unseen(self):
        self._ball.seen = False

    def is_ball_seen_now(self) -> bool:
        return self._ball.seen

    def is_ball_seen_recently(self) -> bool:
        if self._ball.timestamp is None:
            return False
        else:
            return self._ball.timestamp > (time.time() - 2)

    def is_ball_close(self) -> bool:
        return (
                self._ball.seen
                and self._ball.diameter is not None
                and self._ball.diameter > (self._config.detector.ball_close_diameter - 10)
        )