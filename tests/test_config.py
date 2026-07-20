from robot_soccer.config import Config


def test_config_loads_toml_sections_as_attributes(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        [servos]
        rate = 10
        kp = 0.08

        [[detector.classes]]
        name = "ball"
        threshold = 0.7
        """,
        encoding="utf-8",
    )

    config = Config(config_path)

    assert config.path == config_path
    assert config.servos.rate == 10
    assert config.servos.kp == 0.08
    assert config.detector.classes[0].name == "ball"
    assert config.detector.classes[0].threshold == 0.7


def test_to_object_leaves_scalar_values_unchanged():
    assert Config._to_object("sounds") == "sounds"
    assert Config._to_object(10) == 10
