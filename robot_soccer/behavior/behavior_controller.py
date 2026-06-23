import math
import threading
import time
from threading import Thread
from typing import Optional

from robot_soccer.audio.audio_controller import AudioController, Sound
from robot_soccer.behavior.states import Behavior
from robot_soccer.config import Config
from robot_soccer.control.body_controller import BodyController
from robot_soccer.control.head_controller import HeadController
from robot_soccer.state import SharedState
from robot_soccer.timing import Rate


class BehaviorController:
    def __init__(self, shared_state: SharedState, body: BodyController, head: HeadController, audio: AudioController, config: Config):
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

            match behavior:
                case Behavior.BOOTING:
                    self._run_booting()

                case Behavior.SEARCH_BALL:
                    self._run_search_ball()

                case Behavior.FOLLOW_BALL:
                    self._run_follow_ball()

                case Behavior.DONE:
                    self._run_done()

                case _:
                    self._run_done()

            self._rate.sleep()

    def _run_booting(self):
        print("Booting...")
        self._body.hold() # Aucun mouvements
        self._audio.play(sound=Sound.HELLO)
        time.sleep(2) # Attendre
        self._shared_state.set_behavior(Behavior.SEARCH_BALL) # Chercher la balle

    def _run_search_ball(self):
        def search(flag: threading.Event):
            if self._head.circle_until_detected():
                found(flag)

        def move(flag: threading.Event):
            while True:
                time.sleep(3)
                if flag.is_set() or not self._shared_state.is_running: break
                self._body.move(yaw=0.5)

        def timeout(flag: threading.Event):
            while True:
                time.sleep(10)
                if flag.is_set() or not self._shared_state.is_running: break
                self._audio.play(sound=Sound.CANT_FIND_BALL)

        def found(flag: threading.Event):
            self._audio.play(sound=Sound.BALL_FOUND)
            self._shared_state.set_behavior(Behavior.FOLLOW_BALL)
            self._body.hold()
            flag.set()  # Arrêt du mouvement

        print("Searching ball...")
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
        def look(flag: threading.Event):
            while not flag.is_set() and self._shared_state.is_running:
                if self._shared_state.is_ball_recently_seen():
                    self._head.stare_ball()
                self._rate.sleep()

        def walk(flag: threading.Event):
            ln = math.log
            since: float = time.time()

            while not flag.is_set() and self._shared_state.is_running:
                if not self._shared_state.is_ball_close() and self._shared_state.is_ball_seen():
                    since = time.time()
                    self._audio.play(sound=Sound.GETTING_CLOSER)

                    while not flag.is_set() and self._shared_state.is_running:
                        # Ball trouvée
                        if not self._shared_state.is_ball_close() and self._shared_state.is_ball_seen():
                            diameter = self._shared_state.get_ball().diameter
                            surge = ln(max(1.0, self._config.detector.near_ball_px_diameter - diameter)) / self._config.body.caution_factor
                            self._body.move(surge=surge)
                            self._rate.sleep()

                        # Balle proche
                        elif self._shared_state.is_ball_close():
                            since = time.time()
                            self._body.hold()
                            self._audio.play(sound=Sound.GOOD_DISTANCE)
                            break

                        # Balle perdue
                        else:
                            since = time.time()
                            self._body.hold()
                            self._audio.play(sound=Sound.BALL_LOST)
                            break

                elif self._shared_state.is_ball_close() and self._shared_state.is_ball_recently_seen():
                    if time.time() - since >= 3:
                        goal(flag)

                else:
                    if time.time() - since >= 10:
                        lost(flag)

                self._rate.sleep()

        def lost(flag: threading.Event):
            if not flag.is_set():
                flag.set()
                self._body.hold()
                self._audio.play(sound=Sound.CANT_FIND_BALL)
                self._shared_state.set_behavior(Behavior.SEARCH_BALL)

        def goal(flag: threading.Event):
            if not flag.is_set():
                flag.set()
                self._body.hold()
                self._shared_state.set_behavior(Behavior.DONE)


        print("Following ball...")
        flag = threading.Event()  # Event de fin
        threads = [
            Thread(target=look, args=(flag,), daemon=True),
            Thread(target=walk, args=(flag,), daemon=True),
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
