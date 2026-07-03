import math
import threading
import time
from threading import Thread
from typing import Optional

from robot_soccer.audio.audio_controller import AudioController, Sound
from robot_soccer.behavior import health_check
from robot_soccer.behavior.health_check import HealthCheck
from robot_soccer.behavior.states import Behavior
from robot_soccer.config import Config
from robot_soccer.control.body_controller import BodyController
from robot_soccer.control.head_controller import HeadController
from robot_soccer.state import SharedState
from robot_soccer.timing import Rate


class BehaviorController:
    def __init__(self, shared_state: SharedState, body: BodyController, head: HeadController, audio: AudioController, config: Config, health_check: HealthCheck):
        self._health_check = health_check
        self._config = config
        self._audio = audio
        self._head = head
        self._body = body
        self._shared_state = shared_state
        self._thread: Optional[threading.Thread] = None
        self._rate = Rate(10)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self):
        while self._shared_state.is_running:
            behavior = self._shared_state.get_behavior()

            if behavior == Behavior.BOOTING:
                self._run_booting()
            elif behavior == Behavior.SEARCH_BALL:
                self._run_search_ball()
            elif behavior == Behavior.FOLLOW_BALL:
                self._run_follow_ball()
            elif behavior == Behavior.DONE:
                self._run_done()
            else:
                self._run_done()

            self._rate.sleep()

    def _run_booting(self):
        self._body.hold() # Aucun mouvements
        self._audio.play(sound=Sound.HELLO, wait=True)
        if not self._health_check.start():
            self._audio.play(sound=Sound.CANT_ACCESS_SENSORS, wait=True)
        self._shared_state.set_behavior(Behavior.SEARCH_BALL) # Chercher la balle

    def _run_search_ball(self):
        def search(flag: threading.Event):
            if self._head.circle_until_detected():
                found(flag)

        def move(flag: threading.Event):
            while True:
                time.sleep(3)
                if flag.is_set() or not self._shared_state.is_running: break
                self._body.move(yaw=1)

        def timeout(flag: threading.Event):
            while True:
                time.sleep(10)
                if flag.is_set() or not self._shared_state.is_running: break
                self._audio.play(sound=Sound.CANT_FIND_BALL)

        def found(flag: threading.Event):
            self._audio.play(sound=Sound.BALL_FOUND)
            self._body.hold() # Arrêt du mouvement
            self._shared_state.set_behavior(Behavior.FOLLOW_BALL) # Modifier la prochaine étape
            flag.set() # Enclencher la prochaine étape

        self._audio.play(sound=Sound.LOOKING_AROUND)
        flag = threading.Event() # Event de fin
        threads = [
            Thread(target=move, args=(flag,), daemon=True),
            Thread(target=search, args=(flag,), daemon=True),
            Thread(target=timeout, args=(flag,), daemon=True),
        ]
        for thread in threads: thread.start()
        flag.wait() # Attendre l'event de fin
        self._body.hold()

    def _run_follow_ball(self):
        def camera_follow(flag: threading.Event, unseen: threading.Event):
            while not flag.is_set() or self._shared_state.is_running:
                self._head.stare_ball()
                self._rate.sleep()
                if not self._shared_state.is_ball_seen_recently(): unseen.set()
                else: unseen.clear()

        def move(flag: threading.Event):
            play_good_distance: bool = True
            play_getting_closer: bool = True

            while not flag.is_set() or self._shared_state.is_running:
                surge: float = 0.0
                yaw: float = 0.0

                # surge
                if self._shared_state.is_ball_seen_now(): # Si la balle est vue
                    diameter = self._shared_state.get_ball().diameter
                    if diameter < self._config.detector.ball_close2_diameter:  # Balle lointaine
                        play_good_distance = True
                        surge = 0.8
                        if play_getting_closer:
                            play_getting_closer = False
                            self._audio.play(sound=Sound.GETTING_CLOSER)
                    elif diameter < self._config.detector.ball_close1_diameter:
                        surge = 0.3
                    elif diameter > self._config.detector.ball_close1_diameter:
                        play_getting_closer = True
                        if play_good_distance:
                            play_good_distance = False
                            self._audio.play(sound=Sound.GOOD_DISTANCE)
                    else:
                        pass

                # yaw
                if self._shared_state.is_ball_seen_recently():
                    head_yaw = self._shared_state.get_head().yaw
                    if abs(head_yaw) > 40:
                        yaw = math.copysign(1.0, head_yaw)
                        surge = min(0.2, surge)
                    elif abs(head_yaw) > 30:
                        yaw = math.copysign(0.8, head_yaw)
                        surge = min(0.3, surge)
                    elif abs(head_yaw) > 15:
                        yaw = math.copysign(0.5, head_yaw)

                self._body.move(surge=surge, yaw=yaw)
                self._rate.sleep()

        def timeout(flag: threading.Event, unseen: threading.Event):
            while not flag.is_set() or self._shared_state.is_running:
                unseen.wait()
                time.sleep(5)
                if unseen.is_set():
                    self._shared_state.set_behavior(Behavior.SEARCH_BALL)
                    flag.set()

        flag = threading.Event()  # Event de fin
        unseen = threading.Event()  # Event de fin
        threads = [
            Thread(target=camera_follow, args=(flag,unseen,), daemon=True),
            Thread(target=move, args=(flag,), daemon=True),
            Thread(target=timeout, args=(flag,unseen,), daemon=True),
        ]
        for thread in threads: thread.start()
        flag.wait()  # Attendre l'event de fin
        self._body.hold()

    def _run_done(self):
        print("Done !")
        self._body.hold()
        self._audio.play(sound=Sound.KICK)
        time.sleep(5)
        self._shared_state.set_behavior(Behavior.BOOTING)
