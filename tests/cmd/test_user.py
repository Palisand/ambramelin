import argparse
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ambramelin.cmd import user
from ambramelin.util.config import Config, Environment, User
from ambramelin.util.errors import (
    NoUsersError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ambramelin.util.output import (
    MSG_NO_ENV_SELECTED,
    MSG_NO_USER_FOR_CURR_ENV,
    MSG_NO_USERS_ADDED,
)
from tests.conftest import DummyCredentialManager


@pytest.fixture(autouse=True)
def mock_getpass(mocker: MockerFixture) -> None:
    mocker.patch.object(user, "getpass", return_value="password")


class TestAdd:
    def test_success(
        self, config: Config, dummy_creds_manager: DummyCredentialManager
    ) -> None:
        result = user.cmd_add(argparse.Namespace(name="username", creds="dummy"))
        assert result == {"username": {"credentials_manager": "dummy"}}
        assert config == Config(users={"username": User(credentials_manager="dummy")})
        assert dummy_creds_manager.get_password("username") == "password"

    @pytest.mark.parametrize(
        "config",
        (Config(users={"username": User(credentials_manager="dummy")}),),
        indirect=True,
    )
    def test_failure_user_exists(self, config: Config) -> None:
        with pytest.raises(UserAlreadyExistsError):
            user.cmd_add(argparse.Namespace(name="username", creds="dummy"))


class TestCurrent:
    @pytest.mark.parametrize(
        "config,result",
        (
            (
                Config(
                    current="envname",
                    envs={"envname": Environment(url="", user="username")},
                ),
                "username",
            ),
            (
                Config(
                    current="envname",
                    envs={"envname": Environment(url="", user=None)},
                ),
                MSG_NO_USER_FOR_CURR_ENV.format(env="envname"),
            ),
            (Config(), MSG_NO_ENV_SELECTED),
        ),
    )
    def test_success(self, mocker: MockerFixture, config: Config, result: str) -> None:
        mocker.patch.object(user, "load_config", return_value=config)
        assert user.cmd_current(argparse.Namespace()) == result


class TestDel:
    @pytest.mark.parametrize(
        "config",
        (
            Config(
                envs={
                    "env1": Environment(url="", user="user1"),
                    "env2": Environment(url="", user="user2"),
                    "env3": Environment(url="", user="user1"),
                },
                users={
                    "user1": User(credentials_manager="dummy"),
                    "user2": User(credentials_manager="dummy"),
                },
            ),
        ),
        indirect=True,
    )
    def test_success(
        self, config: Config, dummy_creds_manager: DummyCredentialManager
    ) -> None:
        dummy_creds_manager.set_password("user1", "password")
        assert dummy_creds_manager.password_exists("user1")
        user.cmd_del(argparse.Namespace(name="user1"))
        assert config == Config(
            envs={
                "env1": Environment(url="", user=None),
                "env2": Environment(url="", user="user2"),
                "env3": Environment(url="", user=None),
            },
            users={
                "user2": User(credentials_manager="dummy"),
            },
        )
        assert not dummy_creds_manager.password_exists("user1")

    def test_failure_no_users_added(self) -> None:
        with pytest.raises(NoUsersError):
            user.cmd_del(argparse.Namespace(name="user"))

    @pytest.mark.parametrize(
        "config",
        (Config(users={"other-user": User(credentials_manager="keychain")}),),
        indirect=True,
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            user.cmd_del(argparse.Namespace(name="user"))


class TestList:
    @pytest.mark.parametrize(
        "config,result",
        (
            (
                Config(
                    users={
                        "user1": User(credentials_manager="keychain"),
                        "user2": User(credentials_manager="keychain"),
                    }
                ),
                "\n".join(("user1", "user2")),
            ),
            (
                Config(
                    current="env2",
                    envs={
                        "env1": Environment(url="", user="user1"),
                        "env2": Environment(url="", user="user2"),
                    },
                    users={
                        "user1": User(credentials_manager="keychain"),
                        "user2": User(credentials_manager="keychain"),
                        "user3": User(credentials_manager="keychain"),
                    },
                ),
                "\n".join(("user1", "[CURRENT] user2", "user3")),
            ),
            (Config(), MSG_NO_USERS_ADDED),
        ),
    )
    def test_success(self, mocker: MockerFixture, config: Config, result: str) -> None:
        mocker.patch.object(user, "load_config", return_value=config)
        assert user.cmd_list(argparse.Namespace()) == result


class TestSet:
    @pytest.mark.parametrize(
        "args",
        (
            {"creds": None, "passwd": True},
            {"creds": "dummy", "passwd": None},
            {"creds": "dummy", "passwd": True},
        ),
    )
    @pytest.mark.parametrize(
        "config",
        (Config(users={"username": User(credentials_manager="mock")}),),
        indirect=True,
    )
    def test_success(
        self,
        config: Config,
        args: dict,
        dummy_creds_manager: DummyCredentialManager,
        mock_creds_manager: MagicMock,
    ) -> None:
        result = user.cmd_set(argparse.Namespace(name="username", **args))
        assert result == {"username": {"credentials_manager": args["creds"] or "mock"}}
        assert config == Config(
            users={"username": User(credentials_manager=args["creds"] or "mock")}
        )

        if args["creds"] is not None:
            mock_creds_manager.del_password.assert_called_once_with("username")
            assert dummy_creds_manager.get_password("username") == "password"

        elif args["passwd"]:
            mock_creds_manager.del_password.assert_called_once_with("username")
            mock_creds_manager.set_password.assert_called_once_with(
                "username", "password"
            )

    def test_failure_no_users_added(self) -> None:
        with pytest.raises(NoUsersError):
            user.cmd_set(argparse.Namespace(name="user"))

    @pytest.mark.parametrize(
        "config", (Config(users={"other-user": User(credentials_manager="keychain")}),)
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            user.cmd_set(argparse.Namespace(name="user"))
