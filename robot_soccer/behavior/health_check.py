from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from sympy import false

from robot_soccer.audio.audio_controller import Sound, AudioController
from robot_soccer.config import Config
from robot_soccer.ros.ros2_bridge import Ros2Bridge
from robot_soccer.state import SharedState


@dataclass(frozen=True)
class TopicHealthCheck:
    name: str
    topic: str
    ok: bool
    age_seconds: Optional[float]
    details: str


@dataclass(frozen=True)
class Ros2HealthCheck:
    ok: bool
    topics: list[TopicHealthCheck]

    def failed_topics(self) -> list[TopicHealthCheck]:
        return [topic for topic in self.topics if not topic.ok]


@dataclass(frozen=True)
class _TopicProbe:
    name: str
    topic: str
    timestamp_reader: Callable[[], Optional[float]]
    payload_reader: Callable[[], bool]


class HealthCheck:
    def __init__(self, config: Config, ros2_bridge: Ros2Bridge, shared_state: SharedState):
        self._config = config
        self._ros2_bridge = ros2_bridge
        self._shared_state = shared_state

    def start(self) -> bool:
        return (
            self._ros2_bridge_tests()
        )

    def _ros2_bridge_tests(self) -> bool:
        print("Starting Health Check")

        if not self._config.ros2.enabled:
            print("ROS2 disabled, skipping ROS2 health check")
            return True

        print("Testing ROS2")
        result = self._check_ros2_subscribed_topics()
        self._print_ros2_result(result)

        if not result.ok:
            missing_topics = ", ".join(topic.topic for topic in result.failed_topics())
            print(RuntimeError(f"ROS2 health check failed, no fresh data on: {missing_topics}"))

        return result.ok

    def _check_ros2_subscribed_topics(
            self,
            timeout_seconds: float = 5.0,
            max_age_seconds: float = 2.0,
            poll_interval_seconds: float = 0.05,
    ) -> Ros2HealthCheck:
        probes = self._build_ros2_topic_probes()
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            result = self._read_ros2_topic_health(probes, max_age_seconds)
            if result.ok:
                return result
            time.sleep(poll_interval_seconds)

        return self._read_ros2_topic_health(probes, max_age_seconds)

    def _build_ros2_topic_probes(self) -> list[_TopicProbe]:
        topics = self._ros2_bridge.get_subscribed_topics()

        return [
            _TopicProbe(
                name="camera",
                topic=topics["camera"],
                timestamp_reader=lambda: self._shared_state.get_image().timestamp,
                payload_reader=lambda: self._shared_state.get_image().raw is not None,
            ),
            _TopicProbe(
                name="head_servos_state",
                topic=topics["head_servos_state"],
                timestamp_reader=lambda: self._shared_state.get_head().timestamp,
                payload_reader=lambda: (
                    self._shared_state.get_head().yaw is not None
                    and self._shared_state.get_head().pitch is not None
                ),
            ),
        ]

    def _read_ros2_topic_health(self, probes: list[_TopicProbe], max_age_seconds: float) -> Ros2HealthCheck:
        topics = [self._read_topic_health(probe, max_age_seconds) for probe in probes]
        return Ros2HealthCheck(
            ok=all(topic.ok for topic in topics),
            topics=topics,
        )

    def _read_topic_health(self, probe: _TopicProbe, max_age_seconds: float) -> TopicHealthCheck:
        timestamp = probe.timestamp_reader()
        has_payload = probe.payload_reader()

        if timestamp is None:
            return TopicHealthCheck(
                name=probe.name,
                topic=probe.topic,
                ok=False,
                age_seconds=None,
                details="no message received",
            )

        age_seconds = time.time() - timestamp
        if age_seconds > max_age_seconds:
            return TopicHealthCheck(
                name=probe.name,
                topic=probe.topic,
                ok=False,
                age_seconds=age_seconds,
                details=f"last message too old ({age_seconds:.2f}s)",
            )

        if not has_payload:
            return TopicHealthCheck(
                name=probe.name,
                topic=probe.topic,
                ok=False,
                age_seconds=age_seconds,
                details="message received but payload is incomplete",
            )

        return TopicHealthCheck(
            name=probe.name,
            topic=probe.topic,
            ok=True,
            age_seconds=age_seconds,
            details="fresh data received",
        )

    def _print_ros2_result(self, result: Ros2HealthCheck) -> None:
        for topic in result.topics:
            status = "OK" if topic.ok else "FAILED"
            age = "n/a" if topic.age_seconds is None else f"{topic.age_seconds:.2f}s"
            print(f"[{status}] {topic.name} {topic.topic} age={age} - {topic.details}")
