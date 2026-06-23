from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Tuple

from ultralytics import YOLO

from shared_state import Image, Ball


class YoloDetector:
    def __init__(self, model_path: str, confidence_threshold: float) -> None:
        model_path = Path(model_path)

        if not model_path.is_file():
            raise FileNotFoundError(f"File not found or not a regular file: {model_path}")

        print("Loading YOLO detector")
        self._model = YOLO(str(model_path))
        self._confidence_threshold = confidence_threshold
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
        ball: Optional[Ball] = None
        best_confidence = self._confidence_threshold

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
                if width <= 0.0 or height <= 0.0:
                    continue

                best_confidence = confidence_value
                ball = Ball (
                    x = x_min + width / 2.0,
                    y = y_min + height / 2.0,
                    distance = 0,
                    timestamp = time.time(),
                    confidence = confidence
                )

        return ball
