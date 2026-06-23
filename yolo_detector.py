from __future__ import annotations

import time
from pathlib import Path
from statistics import mean
from typing import Optional, Tuple

from fontTools.ttLib.tables.otTables import DeltaSetIndexMap
from ultralytics import YOLO

from config import Config
from shared_state import Image, Ball


class YoloDetector:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._model_path = Path(self._config.detector.yolo_model_path)
        self._confidence_threshold = self._config.detector.yolo_confidence_threshold

        if not self._model_path.is_file():
            raise FileNotFoundError(f"File not found or not a regular file: {self._model_path}")

        print("Loading YOLO detector")
        self._model = YOLO(str(self._model_path))
        print("YOLO detector ready")

    def detect_ball(self, image: Image) -> Optional[Ball]:
        """
        Return None if no ball is detected.

        Otherwise returns:
        x, y position of the ball center in the image.
        """
        frame = image.raw
        if frame is None:
            return None

        results = self._model(frame, verbose=False, device=0)
        best_confidence = self._confidence_threshold
        biggest_ball: Optional[Ball] = None

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue

            xyxy = boxes.xyxy.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            for coords, confidence in zip(xyxy, confidences):
                confidence_value = float(confidence)
                if confidence_value < best_confidence:
                    continue

                x_min, y_min, x_max, y_max = [float(value) for value in coords[:4]]
                width = max(0.0, x_max - x_min)
                height = max(0.0, y_max - y_min)
                x, y = x_min + width / 2.0, y_min + height / 2.0
                diameter = mean([width, height])

                if width <= 0.0 or height <= 0.0:
                    continue

                best_confidence = confidence_value
                ball: Ball = Ball(
                    x=x,
                    y=y,
                    error_x=self._config.camera.width / 2.0 - x,
                    error_y=self._config.camera.height / 2.0 - y,
                    diameter=diameter,
                    timestamp=time.time(),
                    confidence=confidence,
                    seen=True
                )

                if biggest_ball is None:
                    biggest_ball = ball
                elif biggest_ball.diameter < diameter:
                    biggest_ball = ball

        return biggest_ball
