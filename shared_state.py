import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass()
class Head:
    mode: int = 0
    yaw: float = 0.0
    pitch: float = 0.0
    timestamp: float = None

@dataclass()
class Ball:
    x: float = 0.0
    y: float = 0.0
    distance: float = 0.0
    timestamp: float = None
    confidence: float = 0.0

@dataclass()
class Image:
    raw: Optional[np.ndarray] = None
    timestamp: float = None


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._ball = Ball()
        self._head = Head()
        self._image = Image()
        self.is_running = True

    def get_image(self) -> Image:
        return self._image

    def set_image(self, image: Optional[np.ndarray] = None, timestamp: float = time.time() ) -> None:
        with self._lock:
            if image is not None:
                self._image.raw = image
                self._image.timestamp = timestamp

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

