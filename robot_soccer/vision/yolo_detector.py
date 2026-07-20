from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Optional

from sympy.strategies.core import switch
from ultralytics import YOLO
from ultralytics.engine.results import Results

from robot_soccer.config import Config
from robot_soccer.state import Ball, Image, Goal, YoloDetection, YoloCoordinates


class YoloDetector:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._model_path = Path(self._config.detector.yolo_model_path)
        self._classes: list[str] = list(vars(self._config.classes.labels).values())
        self._confidence_thresholds: list[float] = list(vars(self._config.classes.threshold).values())

        if not self._model_path.is_file():
            raise FileNotFoundError(f"File not found or not a regular file: {self._model_path}")

        print("Loading YOLO detector")
        self._model = YOLO(str(self._model_path))
        print("YOLO detector ready")

    def detect(self, image: Image) -> YoloDetection:
        """
        Return None if no ball is detected.

        Otherwise returns:
        x, y position of the ball center in the image.
        """
        frame = image.raw
        if frame is None: return YoloDetection()

        result: Results = self._model(frame, verbose=False, device=0)[0]
        boxes = getattr(result, "boxes", [])
        if boxes is None or len(boxes) == 0: return YoloDetection()

        best_confidence: list[float] = self._confidence_thresholds.copy()
        yd = YoloDetection()

        for box in boxes:
            coords = box.xyxy[0].cpu().tolist()
            confidence = float(box.conf[0].item())
            class_id = int(box.cls[0].item())

            if not 0 <= class_id < len(self._classes):
                continue

            if confidence < best_confidence[class_id]:
                continue

            best_confidence[class_id] = confidence

            x_min, y_min, x_max, y_max = (
                float(value)
                for value in coords
            )

            xy = YoloCoordinates(
                x_min=int(x_min),
                y_min=int(y_min),
                x_max=int(x_max),
                y_max=int(y_max),
            )

            width = max(0.0, x_max - x_min)
            height = max(0.0, y_max - y_min)

            if width <= 0.0 or height <= 0.0:
                continue

            x = x_min + width / 2.0
            y = y_min + height / 2.0
            diameter = (width + height) / 2.0

            error_x = self._config.camera.width / 2.0 - x
            error_y = self._config.camera.height / 2.0 - y

            if self._classes[class_id] == "ball":
                yd.ball = Ball(
                    x=x,
                    y=y,
                    error_x=error_x,
                    error_y=error_y,
                    diameter=diameter,
                    timestamp=time.time(),
                    confidence=confidence,
                    seen=True,
                    _box=xy,
                )

            elif self._classes[class_id] == "goal":
                yd.goal = Goal(
                    x=x,
                    y=y,
                    error_x=error_x,
                    error_y=error_y,
                    width=width,
                    timestamp=time.time(),
                    confidence=confidence,
                    seen=True,
                    _box=xy,
                )

        return yd
