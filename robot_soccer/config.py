from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional, Union

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class Config:
    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self.audio = None
        self.body = None
        self.servos = None
        self.camera = None
        self.detector = None
        self.ros2 = None

        self.path = Path(path) if path is not None else Path(__file__).parents[1] / "config.toml"
        data = self._load_toml(self.path)

        for key, value in data.items():
            setattr(self, key, self._to_object(value))

    @staticmethod
    def _load_toml(path: Path) -> Dict[str, Any]:
        with path.open("rb") as file:
            return tomllib.load(file)

    @classmethod
    def _to_object(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return SimpleNamespace(**{key: cls._to_object(item) for key, item in value.items()})

        if isinstance(value, list):
            return [cls._to_object(item) for item in value]

        return value
