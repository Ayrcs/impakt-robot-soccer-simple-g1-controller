import threading
import time
from typing import Optional

from robot_soccer.config import Config
from robot_soccer.state import Ball, Image, SharedState
from robot_soccer.timing import Rate
from robot_soccer.vision.yolo_detector import YoloDetector


class VisionWorker:
    def __init__(self, shared_state: SharedState, config: Config) -> None:
        self._shared_state: SharedState = shared_state
        self._config: Config = config
        self._thread: Optional[threading.Thread] = None
        self._rate: Rate = Rate(self._config.detector.rate)
        self.yolo_detector: YoloDetector = YoloDetector(config=self._config)

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
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        print("Vision module started")
        while self._shared_state.is_running:
            image: Image = self._shared_state.get_image()
            if image.raw is None:
                self._rate.sleep()
                continue

            detected_ball: Optional[Ball] = self.yolo_detector.detect_ball(image=image)
            if detected_ball is None:
                if self._shared_state.is_ball_seen_now():
                    self._shared_state.set_ball_unseen()
                    print("Ball disappeared")
            else:
                print(
                    f"Detected ball at x={detected_ball.x:.1f}, y={detected_ball.y:.1f}, "
                    f"c={detected_ball.confidence:.2f}, d={detected_ball.diameter:.2f}"
                )
                self._shared_state.set_ball(detected_ball)

        print("Vision module ended")
