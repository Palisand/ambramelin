import json
from pathlib import Path
from typing import TypedDict, Optional


# TODO: https://stackoverflow.com/a/55176692/3446870


class Environment(TypedDict):
    url: str
    user: Optional[str]


class Config(TypedDict):
    envs: dict[str, Environment]
    current: Optional[str]


def load_config() -> Config:
    file = Path("config.json")  # TODO: belongs elsewhere: ~/.ambramelin/config

    if file.exists():
        with file.open("r") as f:
            return json.loads(f.read())

    return {"envs": {}, "current": None}


def set_config(config: Config) -> None:
    file = Path("config.json")

    with file.open("w") as f:
        f.write(json.dumps(config, indent=2))
