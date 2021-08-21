import contextlib
import json
from pathlib import Path
from typing import TypedDict, Optional, ContextManager


# TODO: https://stackoverflow.com/a/55176692/3446870


class User(TypedDict):
    credentials_manager: str


class Environment(TypedDict):
    url: str
    user: Optional[str]


class Config(TypedDict):
    current: Optional[str]
    envs: dict[str, Environment]
    users: dict[str, User]


def _get_empty_config() -> Config:
    return {"current": None, "envs": {}, "users": {}}


def _get_config_path() -> Path:
    # TODO: belongs elsewhere: e.g. ~/.ambramelin/config
    #  allow for specifying via global --config option and AMBRAMELIN_CONFIG_PATH envvar
    return Path("config.json")


def load_config() -> Config:
    file = _get_config_path()

    if file.exists():
        with file.open("r") as f:
            return json.loads(f.read())

    return _get_empty_config()


def save_config(config: Config) -> None:
    file = _get_config_path()

    with file.open("w") as f:
        f.write(json.dumps(config, indent=2))


@contextlib.contextmanager
def update_config() -> ContextManager[Config]:
    config = load_config()
    yield config
    save_config(config)


def envs_added(config: Config) -> bool:
    return bool(config["envs"])


def env_selected(config: Config) -> bool:
    return config["current"] is not None


def env_exists(config: Config, name: str) -> bool:
    return name in config["envs"]


def users_added(config: Config) -> bool:
    return bool(config["users"])


def user_exists(config: Config, name: str) -> bool:
    return name in config["users"]
