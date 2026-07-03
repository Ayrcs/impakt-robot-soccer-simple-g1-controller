import time
from enum import Enum
from pathlib import Path
import wave

from robot_soccer.config import Config
from robot_soccer.ros.ros2_bridge import Ros2Bridge


class Sound(Enum):
    BALL_FOUND = "ball_found.wav"
    BALL_LOST = "ball_lost.wav"
    CANT_ACCESS_SENSORS = "cant_access_sensors.wav"
    CANT_FIND_BALL = "cant_find_ball.wav"
    CANT_SEE = "cant_see.wav"
    CATCH_BALL = "catch_ball.wav"
    ERROR_OCCURED = "error_occured.wav"
    GETTING_CLOSER = "getting_closer.wav"
    GOOD_DISTANCE = "good_distance.wav"
    GOODBYE = "goodbye.wav"
    HELLO = "hello.wav"
    KICK = "kick.wav"
    LOOKING_AROUND = "looking_around.wav"
    SERVERAL_BALLS = "serveral_balls.wav"
    SERVOS_NOT_RESPONDING = "servos_not_responding.wav"
    TRACKING_BALL = "tracking_ball.wav"


class AudioController:
    def __init__(self, ros2_bridge: Ros2Bridge, config: Config):
        self._ros2_bridge: Ros2Bridge = ros2_bridge
        self._config: Config = config
        self._sounds_dir: Path = Path(self._config.audio.path)

    def play(self, sound: Sound, wait: bool = False) -> None:
        wav_path = self._sounds_dir / sound.value
        pcm, duration = self._read_wav_pcm(wav_path)
        self._ros2_bridge.publish_audio(pcm=pcm)
        print(f"Playing sound {sound.value} ({len(pcm)} PCM bytes)")
        if wait:
            time.sleep(duration)

    def _read_wav_pcm(self, path: Path) -> tuple[bytes, float]:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            rate = wav.getframerate()
            width = wav.getsampwidth()
            frames = wav.getnframes()

            if channels != 1:
                raise ValueError(f"WAV must be mono, got {channels} channels: {path}")

            if rate != 16000:
                raise ValueError(f"WAV must be 16000 Hz, got {rate}: {path}")

            if width != 2:
                raise ValueError(f"WAV must be 16-bit PCM, got sample width {width}: {path}")

            pcm = wav.readframes(frames)
            duration = frames / rate
            return pcm, duration
