import threading
import time
from typing import Optional

from config import Config
from shared_state import SharedState, Image, Ball
from yolo_detector import YoloDetector


class VisionBridge:
    def __init__(self, shared_state: SharedState, config: Config) -> None:
        self._shared_state: SharedState = shared_state
        self._config: Config = config
        self._thread: Optional[threading.Thread] = None
        self.yolo_detector: YoloDetector = YoloDetector(model_path=self._config.detector.yolo_model_path, confidence_threshold=self._config.detector.yolo_confidence_threshold)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        time.sleep(1)
        try:
            self._shared_state.save_image()
        except Exception as e:
            print(e)


    def stop(self) -> None:
        self._shared_state.is_running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        print("Vision module started")
        while self._shared_state.is_running:
            image: Image = self._shared_state.get_image()
            if image.raw is None:
                time.sleep(0.05)
                continue

            detected_ball = self.yolo_detector.detect_ball(image=image)
            if detected_ball is not None:
                print(f"Detected ball at x={detected_ball.x:.1f}, y={detected_ball.y:.1f}, confidence={detected_ball.confidence:.2f}")
                self._shared_state.set_ball(detected_ball)

        print("Vision module ended")
