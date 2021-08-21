import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from pytest_mock import MockerFixture

from ambramelin.util import config as util_config


class TestLoadConfig():
    def test_with_file(self, mocker: MockerFixture) -> None:
        config = {"foo": "bar"}

        with NamedTemporaryFile() as conf_file:
            conf_file.write(json.dumps(config).encode())
            conf_file.seek(0)
            mocker.patch.object(
                util_config, "_get_config_path", return_value=Path(conf_file.name)
            )
            assert util_config.load_config() == config

    def test_with_no_file(self, mocker: MockerFixture) -> None:
        mocker.patch.object(
            util_config, "_get_config_path", return_value=Path("nonexistent")
        )
        assert util_config.load_config() == util_config._get_empty_config()


def test_save_config(mocker: MockerFixture) -> None:
    config = {"foo": "bar"}

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        mocker.patch.object(util_config, "_get_config_path", return_value=path)

        util_config.save_config(config)

        with path.open("r") as f:
            assert json.loads(f.read()) == config


def test_update_config(mocker: MockerFixture) -> None:
    mocker.patch.object(util_config, "load_config", return_value={"foo": "bar"})
    mock_save_config = mocker.patch.object(util_config, "save_config",)

    with util_config.update_config() as config:
        config["foo"] = "qux"

    mock_save_config.assert_called_once_with({"foo": "qux"})


@pytest.mark.parametrize(
    "config,result",
    (
        ({"envs": {"env": {}}}, True),
        ({"envs": {}}, False),
    ),
)
def test_envs_added(config: dict, result: bool) -> None:
    assert util_config.envs_added(config) is result


@pytest.mark.parametrize(
    "config,result",
    (
        ({"current": "env"}, True),
        ({"current": None}, False),
    ),
)
def test_env_selected(config: dict, result: bool) -> None:
    assert util_config.env_selected(config) is result


@pytest.mark.parametrize(
    "env_name,result",
    (
        ("env1", True),
        ("env2", False),
    )
)
def test_env_exists(env_name: str, result: bool) -> None:
    assert util_config.env_exists({"envs": {"env1": {}}}, env_name) is result


@pytest.mark.parametrize(
    "config,result",
    (
        ({"users": {"user": {}}}, True),
        ({"users": {}}, False),
    )
)
def test_users_added(config: dict, result: bool) -> None:
    assert util_config.users_added(config) is result


@pytest.mark.parametrize(
    "user_name,result",
    (
        ("user1", True),
        ("user2", False),
    )
)
def test_user_exists(user_name: str, result: bool) -> None:
    assert util_config.user_exists({"users": {"user1": {}}}, user_name) is result
