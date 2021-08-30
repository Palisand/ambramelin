import contextlib
import json
from pathlib import Path
from typing import ContextManager, Optional

import attr
import cattr


@attr.define
class User:
    credentials_manager: str


@attr.define
class Environment:
    url: str
    user: Optional[str] = None


@attr.define
class Config:
    current: Optional[str] = None
    envs: dict[str, Environment] = {}
    users: dict[str, User] = {}


def _get_config_path() -> Path:
    # TODO: belongs elsewhere: e.g. ~/.ambramelin/config
    #  allow for specifying via global --config option and AMBRAMELIN_CONFIG_PATH envvar
    return Path("config.json")


def load_config() -> Config:
    file = _get_config_path()

    if file.exists():
        with file.open("r") as f:
            return cattr.structure(json.loads(f.read()), Config)

    return Config()


def save_config(config: Config) -> None:
    file = _get_config_path()

    with file.open("w") as f:
        f.write(json.dumps(cattr.unstructure(config), indent=2))


@contextlib.contextmanager
def update_config() -> ContextManager[Config]:
    config = load_config()
    yield config
    save_config(config)


def envs_added(config: Config) -> bool:
    return bool(config.envs)


def env_selected(config: Config) -> bool:
    return config.current is not None


def env_exists(config: Config, name: str) -> bool:
    return name in config.envs


def users_added(config: Config) -> bool:
    return bool(config.users)


def user_exists(config: Config, name: str) -> bool:
    return name in config.users
