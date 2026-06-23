from enum import Enum

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
        self._ros2_bridge = ros2_bridge
        self._config = config

    def play(self, sound: Sound):
        print(f"Playing sound {sound.value}")
        pass #TODO: connecter a ROS2