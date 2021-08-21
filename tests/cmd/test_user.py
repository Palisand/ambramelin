import argparse
from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ambramelin.cmd import user
from ambramelin.util import credentials
from ambramelin.util.config import Config
from ambramelin.util.credentials import CredentialManager
from ambramelin.util.errors import (
    UserAlreadyExistsError,
    NoUsersError,
    UserNotFoundError,
)
from ambramelin.util.output import (
    MSG_NO_ENV_SELECTED,
    MSG_NO_USER_FOR_CURR_ENV,
    MSG_NO_USERS_ADDED,
)


class DummyCredentialManager(CredentialManager):
    def __init__(self):
        self._store = {}

    def get_password(self, account: str) -> Optional[str]:
        return self._store.get(account)

    def set_password(self, account: str, password: str) -> None:
        self._store[account] = password

    def del_password(self, account: str) -> None:
        del self._store[account]


@pytest.fixture
def dummy_creds_manager() -> DummyCredentialManager:
    return DummyCredentialManager()


@pytest.fixture
def mock_creds_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture(autouse=True)
def mock_creds_managers_mapping(
    mocker: MockerFixture,
    dummy_creds_manager: DummyCredentialManager,
    mock_creds_manager: MagicMock,
) -> None:
    mocker.patch.object(
        credentials,
        "managers",
        new={"dummy": dummy_creds_manager, "mock": mock_creds_manager}
    )


@pytest.fixture(autouse=True)
def mock_getpass(mocker: MockerFixture) -> None:
    mocker.patch.object(user, "getpass", return_value="password")


class TestAdd:

    def test_success(
        self, config: Config, dummy_creds_manager: DummyCredentialManager
    ) -> None:
        result = user.cmd_add(argparse.Namespace(name="username", creds="dummy"))
        assert result == {"username": {"credentials_manager": "dummy"}}
        assert config == {"current": None, "envs": {}, "users": result}
        assert dummy_creds_manager.get_password("username") == "password"

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"username": {"credentials_manager": "dummy"}},
            },
        ),
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
                {"current": "envname", "envs": {"envname": {"user": "username"}}},
                "username",
            ),
            (
                {"current": "envname", "envs": {"envname": {"user": None}}},
                MSG_NO_USER_FOR_CURR_ENV.format(env="envname"),
            ),
            ({"current": None}, MSG_NO_ENV_SELECTED),
        ),
    )
    def test_success(self, mocker: MockerFixture, config: Config, result: str) -> None:
        mocker.patch.object(user, "load_config", return_value=config)
        assert user.cmd_current(argparse.Namespace()) == result


class TestDel:

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {
                    "env1": {"user": "user1"},
                    "env2": {"user": "user2"},
                    "env3": {"user": "user1"},
                },
                "users": {"user1": {"credentials_manager": "dummy"}, "user2": {}},
            },
        ),
        indirect=True,
    )
    def test_success(self, config: Config, dummy_creds_manager: DummyCredentialManager) -> None:
        dummy_creds_manager.set_password("user1", "password")
        assert dummy_creds_manager.password_exists("user1")
        user.cmd_del(argparse.Namespace(name="user1"))
        assert config == {
            "current": None,
            "envs": {
                "env1": {"user": None},
                "env2": {"user": "user2"},
                "env3": {"user": None},
            },
            "users": {"user2": {}}
        }
        assert not dummy_creds_manager.password_exists("user1")

    def test_failure_no_users_added(self) -> None:
        with pytest.raises(NoUsersError):
            user.cmd_del(argparse.Namespace(name="user"))

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"other-user": {}}
            },
        ),
        indirect=True
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            user.cmd_del(argparse.Namespace(name="user"))


class TestList:

    @pytest.mark.parametrize(
        "config,result",
        (
            (
                {
                    "current": None,
                    "envs": {},
                    "users": {"user1": {}, "user2": {}},
                },
                "\n".join(("user1", "user2")),
            ),
            (
                {
                    "current": "env2",
                    "envs": {
                        "env1": {"user": "user1"},
                        "env2": {"user": "user2"},
                    },
                    "users": {"user1": {}, "user2": {}, "user3": {}},
                },
                "\n".join(("user1", "[CURRENT] user2", "user3")),
            ),
            (
                {"users": {}}, MSG_NO_USERS_ADDED
            ),
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
        )
    )
    @pytest.mark.parametrize(
        "config",
        (
            {
                "users": {
                    "username": {"credentials_manager": "mock"}
                }
            },
        ),
        indirect=True
    )
    def test_success(
        self,
        config: Config,
        args: dict,
        dummy_creds_manager: DummyCredentialManager,
        mock_creds_manager: MagicMock
    ) -> None:
        result = user.cmd_set(argparse.Namespace(name="username", **args))
        assert result == {
            "username": {
                "credentials_manager": args["creds"] or "mock"
            }
        }
        assert config == {"users": result}

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
        "config",
        (
            {
                "users": {"other-user": {}}
            }
        )
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            user.cmd_set(argparse.Namespace(name="user"))
