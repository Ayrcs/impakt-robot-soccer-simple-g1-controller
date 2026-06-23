from setuptools import setup


setup(
    name="impakt-robot-soccer-simple-g1-controller",
    version="0.1.0",
    description="Simple G1 robot soccer controller using ROS 2 camera images.",
    python_requires=">=3.8",
    py_modules=[
        "ball",
        "config",
        "main",
        "ros2_bridge",
        "shared_state",
    ],
    install_requires=[
        "numpy>=1.24,<1.25; python_version < '3.9'",
        "numpy>=1.24; python_version >= '3.9'",
        "opencv-python>=4.8,<4.11; python_version < '3.9'",
        "opencv-python>=4.8; python_version >= '3.9'",
        "tomli>=2.0; python_version < '3.11'",
    ],
)
