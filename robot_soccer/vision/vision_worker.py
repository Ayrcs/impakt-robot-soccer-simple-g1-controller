from __future__ import annotations

import threading
import time
from typing import Optional

import cv2

from robot_soccer.config import Config
from robot_soccer.state import Image, SharedState, YoloDetection
from robot_soccer.timing import Rate
from robot_soccer.vision.yolo_detector import YoloDetector


class VisionWorker:
    def __init__(self, shared_state: SharedState, config: Config) -> None:
        self._shared_state: SharedState = shared_state
        self._config: Config = config
        self._threads: Optional[list[threading.Thread]] = None
        self._rate: Rate = Rate(self._config.detector.rate)
        self.yolo_detector: YoloDetector = YoloDetector(config=self._config)

    def start(self) -> None:
        if self._threads is not None and self._threads[0].is_alive():
            return

        self._threads = [
            threading.Thread(target=self._run, daemon=True),
            threading.Thread(target=self._save_image, daemon=True)
        ]
        for thread in self._threads: thread.start()

    def stop(self) -> None:
        for thread in self._threads:
            thread.join(timeout=5)

    def _run(self) -> None:
        print("Vision module started")
        while self._shared_state.is_running:
            image: Image = self._shared_state.get_image()
            if image.raw is None:
                self._rate.sleep()
                continue

            yd: YoloDetection = self.yolo_detector.detect(image=image)

            if yd.ball:
                print(
                    f"[BALL] Detected ball at x={yd.ball.x:.1f}, y={yd.ball.y:.1f}, "
                    f"c={yd.ball.confidence:.2f}, d={yd.ball.diameter:.2f}"
                )

            if yd.goal:
                print(
                    f"[GOAL] Detected goal at x={yd.goal.x:.1f}, y={yd.goal.y:.1f}, "
                    f"c={yd.goal.confidence:.2f}, w={yd.goal.width:.2f}"
                )

            self._shared_state.set_detected_objects(yolo_detection=yd)

        print("Vision module ended")

    def _save_image(self) -> None:
        time.sleep(1)
        while self._shared_state.is_running:
            image = self._shared_state.get_image()
            goal = self._shared_state.get_goal()
            ball = self._shared_state.get_ball()
            try:
                if image:
                    objects = [goal, ball]
                    for obj in objects:
                        cv2.rectangle(
                            img=image.raw,
                            pt1=(
                                int(obj._box.x_min),
                                int(obj._box.y_min),
                            ),
                            pt2=(
                                int(obj._box.x_max),
                                int(obj._box.y_max),
                            ),
                            thickness=2,
                            color = (255, 0, 0)
                        )

                    dx = goal.x - ball.x
                    dy = goal.y - ball.y

                    scale = self._config.camera.width * 2
                    start = (
                        int(goal.x - scale * dx),
                        int(goal.y - scale * dy),
                    )
                    end = (
                        int(goal.x + scale * dx),
                        int(goal.y + scale * dy),
                    )
                    cv2.line(
                        img=image.raw,
                        pt1=start,
                        pt2=end,
                        color=(0, 0, 255),
                        thickness=1
                    )
                    cv2.imwrite("frames/last_image.jpg", image.raw)
            except Exception as e:
                print("Impossible d'enregistrer la dernière image", e)
            time.sleep(5)
