# Impakt Robot Soccer Simple G1 Controller

Experimental controller for the Unitree G1 robot, developed as part of a
university research project.

This project is currently under development. Its goal is to control a Unitree
G1 robot through high-level control commands, especially locomotion commands,
using ROS 2 and the interfaces provided by Unitree.

## Purpose

This repository contains a Python application that coordinates several modules:

- camera image reception through ROS 2;
- ball detection with a YOLO model;
- head control through the camera servos;
- high-level locomotion command publishing;
- sound playback through the Unitree audio interface;
- simple behavior logic: boot, ball search, ball following, and stop.

The goal is to provide a simple base for experimenting with robot soccer
behaviors on the Unitree G1.

## Status

This project is ongoing research work. The API, configuration, and behaviors may
still change. The code should be used carefully, in a controlled environment,
and under supervision.

## Target Environment

This project is designed to run directly on the Unitree G1 robot.

Main requirements:

- Unitree G1 with the robot environment configured;
- ROS 2 Foxy;
- CycloneDDS as the DDS middleware;
- Unitree ROS messages available, especially `unitree_api` and `unitree_go`;
- Python compatible with ROS 2 Foxy;
- access to the robot camera, servo, sport API, and audio topics.

CycloneDDS must be enabled in the ROS environment before running the project:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

## Installation

From the robot, clone the repository and install the Python package:

```bash
git clone <repository-url>
cd impakt-robot-soccer-simple-g1-controller
python3 -m pip install -e .
```

Make sure the ROS 2 Foxy environment is sourced before launching the application:

```bash
source /opt/ros/foxy/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Depending on the robot setup, you may also need to source the workspace that
contains the Unitree messages.

## Configuration

The main configuration file is `config.toml`.

Important sections:

- `ros2`: ROS 2 topic names used by the application;
- `detector`: detection settings and YOLO model path;
- `camera`: expected image dimensions;
- `servos`: limits and gains for head control;
- `body`: update rate and caution factor for locomotion;
- `audio`: folder containing sound files.

By default, the application uses:

- `/camera/color/image_raw/compressed` for the camera;
- `/g1_comp_servo/cmd` to command the head servos;
- `/g1_comp_servo/state` to read the servo state;
- `/api/sport/request` for high-level locomotion commands;
- `/api/voice/request` for audio.

## Running

Run the application from the repository root:

```bash
python3 main.py
```

The program starts the ROS 2, vision, control, and behavior modules, then keeps
running until interrupted.

To stop it cleanly:

```bash
Ctrl+C
```

## Safety

This software can send movement commands to the robot. Before any test:

- make sure the robot is in a clear area;
- keep a manual stop method accessible;
- verify the ROS 2 topics and movement limits;
- test progressively with low speeds;
- do not run the project on an unsupervised robot.

## License

This project is distributed under the MIT License. See `LICENSE`.
