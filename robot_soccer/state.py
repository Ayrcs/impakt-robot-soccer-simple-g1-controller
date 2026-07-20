from __future__ import annotations

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
    _box: YoloCoordinates = None


@dataclass()
class Goal:
    x: float = None
    y: float = None
    error_x: float = None
    error_y: float = None
    width: float = None
    distance: float = None
    timestamp: float = None
    confidence: float = None
    seen: bool = False
    _box: YoloCoordinates = None


@dataclass
class YoloDetection:
    ball: Optional[Ball] = None
    goal: Optional[Goal] = None


@dataclass
class YoloCoordinates:
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass()
class Image:
    raw: Optional[np.ndarray] = None
    timestamp: float = None


@dataclass()
class Scene:
    ball_goal_dx: float = None
    ball_goal_dy: float = None


class SharedState:
    def __init__(self, config: Config) -> None:
        self._lock = threading.Lock()
        self._ball = Ball()
        self._goal = Goal()
        self._head = Head()
        self._image = Image()
        self._scene = Scene()
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

    def set_detected_objects(self, yolo_detection: YoloDetection) -> None:
        if yolo_detection.ball is None: self._ball.seen = False
        else: self._ball: Ball = yolo_detection.ball

        if yolo_detection.goal is None: self._goal.seen = False
        else: self._goal: Goal = yolo_detection.goal

        if yolo_detection.goal is not None and yolo_detection.ball is not None:
            dx = yolo_detection.goal.x - yolo_detection.ball.x
            dy = yolo_detection.goal.y - yolo_detection.ball.y
            self._scene.ball_goal_dx = dx
            self._scene.ball_goal_dy = dy

    def set_ball(self, ball: Ball) -> None:
        self._ball: Ball = ball

    def set_head(self, head: Head) -> None:
        self._head: Head = head

    def get_ball(self) -> Ball:
        return self._ball

    def get_goal(self) -> Goal:
        return self._goal

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

    def set_goal_unseen(self):
        self._goal.seen = False

    def is_goal_seen_now(self) -> bool:
        return self._goal.seen

    def is_goal_seen_recently(self) -> bool:
        if self._goal.timestamp is None:
            return False
        else:
            return self._goal.timestamp > (time.time() - 2)
