import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import cattr
import pytest
from pytest_mock import MockerFixture

from ambramelin.util import config as util_config
from ambramelin.util.config import Config, Environment, User


class TestLoadConfig:
    def test_with_file(self, mocker: MockerFixture) -> None:
        config = Config(
            current="envname",
            envs={"envname": Environment(url="envurl", user="username")},
            users={"username": User(credentials_manager="dummy")},
        )

        with NamedTemporaryFile() as conf_file:
            conf_file.write(json.dumps(cattr.unstructure(config), indent=2).encode())
            conf_file.seek(0)
            mocker.patch.object(
                util_config, "_get_config_path", return_value=Path(conf_file.name)
            )
            assert util_config.load_config() == config

    def test_with_no_file(self, mocker: MockerFixture) -> None:
        mocker.patch.object(
            util_config, "_get_config_path", return_value=Path("nonexistent")
        )
        assert util_config.load_config() == Config()


def test_save_config(mocker: MockerFixture) -> None:
    config = Config(
        current="envname",
        envs={"envname": Environment(url="envurl", user="username")},
        users={"username": User(credentials_manager="dummy")},
    )

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        mocker.patch.object(util_config, "_get_config_path", return_value=path)

        util_config.save_config(config)

        with path.open("r") as f:
            assert cattr.structure(json.loads(f.read()), Config) == config


def test_update_config(mocker: MockerFixture) -> None:
    mocker.patch.object(util_config, "load_config", return_value=Config())
    mock_save_config = mocker.patch.object(util_config, "save_config")

    with util_config.update_config() as config:
        config.current = "current"

    mock_save_config.assert_called_once_with(config)


@pytest.mark.parametrize(
    "config,result",
    (
        (Config(envs={"env": Environment(url="")}), True),
        (Config(), False),
    ),
)
def test_envs_added(config: Config, result: bool) -> None:
    assert util_config.envs_added(config) is result


@pytest.mark.parametrize(
    "config,result",
    (
        (Config(current="env"), True),
        (Config(), False),
    ),
)
def test_env_selected(config: Config, result: bool) -> None:
    assert util_config.env_selected(config) is result


@pytest.mark.parametrize(
    "env_name,result",
    (
        ("env1", True),
        ("env2", False),
    )
)
def test_env_exists(env_name: str, result: bool) -> None:
    assert util_config.env_exists(
        Config(envs={"env1": Environment(url="")}), env_name
    ) is result


@pytest.mark.parametrize(
    "config,result",
    (
        (Config(users={"user": User(credentials_manager="keychain")}), True),
        (Config(), False),
    )
)
def test_users_added(config: Config, result: bool) -> None:
    assert util_config.users_added(config) is result


@pytest.mark.parametrize(
    "user_name,result",
    (
        ("user1", True),
        ("user2", False),
    )
)
def test_user_exists(user_name: str, result: bool) -> None:
    assert util_config.user_exists(
        Config(users={"user1": User(credentials_manager="keychain")}), user_name
    ) is result
