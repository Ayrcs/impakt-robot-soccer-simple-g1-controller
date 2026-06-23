import signal
import time

from robot_soccer.app import RobotApp


def _request_stop(robot: RobotApp) -> None:
    print("Stopping robot")
    robot.stop()


if __name__ == "__main__":
    # Debug
    # pydevd_pycharm.settrace('localhost', port=2224, stdout_to_server=True, stderr_to_server=True)

    robot = RobotApp()
    signal.signal(signal.SIGTERM, lambda signum, frame: _request_stop(robot))
    robot.start()

    try:
        while robot.shared_state.is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        _request_stop(robot)
    finally:
        robot.stop()
