import argparse

import pytest
from pytest_mock import MockerFixture

from ambramelin.cmd import env
from ambramelin.util.config import Config
from ambramelin.util.errors import (
    EnvironmentAlreadyExistsError,
    EnvironmentNotFoundError,
    NoEnvironmentsError,
    NoUsersError,
    UserNotFoundError,
)
from ambramelin.util.output import MSG_NO_ENV_SELECTED, MSG_NO_ENVS_ADDED


class TestAdd:

    def test_success(self, config: Config) -> None:
        result = env.cmd_add(argparse.Namespace(name="envname", url="ambra.com", user=None))
        assert result == {"envname": {"url": "ambra.com", "user": None}}
        assert config == {"current": None, "envs": result, "users": {}}

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"username": {"credentials_manager": "keychain"}},
            },
        ),
        indirect=True,
    )
    def test_success_with_user(self, config: Config) -> None:
        result = env.cmd_add(
            argparse.Namespace(name="envname", url="ambra.com", user="username")
        )
        assert result == {"envname": {"url": "ambra.com", "user": "username"}}
        assert config == {
            "current": None,
            "envs": result,
            "users": {"username": {"credentials_manager": "keychain"}},
        }

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {"envname": {"url": "ambra.com", "user": None}},
                "users": {},
            },
        ),
        indirect=True,
    )
    def test_failure_env_exists(self, config: Config) -> None:
        with pytest.raises(EnvironmentAlreadyExistsError):
            env.cmd_add(argparse.Namespace(name="envname", url="ambra.com", user=None))

    def test_failure_no_users(self) -> None:
        with pytest.raises(NoUsersError):
            env.cmd_add(
                argparse.Namespace(name="envname", url="ambra.com", user="username")
            )

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"other-username": {"credentials_manager": "keychain"}},
            },
        ),
        indirect=True,
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            env.cmd_add(
                argparse.Namespace(name="envname", url="ambra.com", user="username")
            )


class TestCurrent:

    @pytest.mark.parametrize(
        "config,result",
        (
            ({"current": "envname"}, "envname"),
            ({"current": None}, MSG_NO_ENV_SELECTED),
        ),
    )
    def test_success(self, mocker: MockerFixture, config: Config, result: str) -> None:
        mocker.patch.object(env, "load_config", return_value=config)
        assert env.cmd_current(argparse.Namespace()) == result


class TestDel:

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": "env1",
                "envs": {"env1": {}, "env2": {}},
                "users": {},
            },
        ),
        indirect=True,
    )
    def test_success(self, config: Config) -> None:
        env.cmd_del(argparse.Namespace(name="env1"))
        assert config == {
            "current": None,
            "envs": {"env2": {}},
            "users": {},
        }

    def test_failure_no_envs_added(self) -> None:
        with pytest.raises(NoEnvironmentsError):
            env.cmd_del(argparse.Namespace(name="env"))

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {"other-env": {}},
                "users": {},
            },
        ),
        indirect=True,
    )
    def test_failure_env_not_found(self, config: Config) -> None:
        with pytest.raises(EnvironmentNotFoundError):
            env.cmd_del(argparse.Namespace(name="env"))


class TestList:

    @pytest.mark.parametrize(
        "config,result",
        (
            (
                {
                    "current": None,
                    "envs": {
                        "env1": {"url": "url1"}, "env2": {"url": "url2"}
                    },
                },
                "\n".join(("env1: url1", "env2: url2"))
            ),
            (
                {
                    "current": "env2",
                    "envs": {
                        "env1": {"url": "url1"},
                        "env2": {"url": "url2"},
                        "env3": {"url": "url3"},
                    },
                },
                "\n".join(
                    (
                        "env1: url1",
                        "[CURRENT] env2: url2",
                        "env3: url3"
                    )
                )
            ),
            (
                {"envs": {}}, MSG_NO_ENVS_ADDED
            ),
        )
    )
    def test_success(self, mocker: MockerFixture, config: Config, result: str) -> None:
        mocker.patch.object(env, "load_config", return_value=config)
        assert env.cmd_list(argparse.Namespace()) == result


class TestSet:
    @pytest.mark.parametrize(
        "args",
        (
            {"url": "new.com", "user": None},
            {"url": None, "user": "new-user"},
            {"url": "new.com", "user": "new-user"},
        )
    )
    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {
                    "envname": {"url": "old.com", "user": "old-user"},
                },
                "users": {
                    "old-user": {"credentials_manager": "keychain"},
                    "new-user": {"credentials_manager": "keychain"},
                },
            },
        ),
        indirect=True
    )
    def test_success(self, config: Config, args: dict) -> None:
        result = env.cmd_set(argparse.Namespace(name="envname", **args))
        assert result == {
            "envname": {
                "url": args["url"] or "old.com",
                "user": args["user"] or "old-user",
            }
        }
        assert config == {
            "current": None,
            "envs": result,
            "users": {
                "old-user": {"credentials_manager": "keychain"},
                "new-user": {"credentials_manager": "keychain"},
            },
        }

    def test_failure_no_envs_added(self) -> None:
        with pytest.raises(NoEnvironmentsError):
            env.cmd_set(argparse.Namespace(name="env"))

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {"other-env": {}},
                "users": {},
            },
        ),
        indirect=True,
    )
    def test_failure_env_not_found(self, config: Config) -> None:
        with pytest.raises(EnvironmentNotFoundError):
            env.cmd_set(argparse.Namespace(name="env"))

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {
                    "envname": {"url": "old.com", "user": None},
                },
                "users": {},
            },
        ),
        indirect=True
    )
    def test_failure_no_users(self, config: Config) -> None:
        with pytest.raises(NoUsersError):
            env.cmd_set(
                argparse.Namespace(name="envname", url="ambra.com", user="username")
            )

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {
                    "envname": {"url": "old.com", "user": "old-user"},
                },
                "users": {"old-user": {"credentials_manager": "keychain"}},
            },
        ),
        indirect=True,
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            env.cmd_set(
                argparse.Namespace(name="envname", url="ambra.com", user="username")
            )


class TestUse:
    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {
                    "envname": {"url": "old.com", "user": None},
                },
                "users": {},
            },
        ),
        indirect=True
    )
    def test_success(self, config: Config) -> None:
        env.cmd_use(argparse.Namespace(name="envname"))
        assert config == {
            "current": "envname",
            "envs": {
                "envname": {"url": "old.com", "user": None},
            },
            "users": {},
        }

    def test_failure_no_envs_added(self) -> None:
        with pytest.raises(NoEnvironmentsError):
            env.cmd_use(argparse.Namespace(name="env"))

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {"other-env": {}},
                "users": {},
            },
        ),
        indirect=True,
    )
    def test_failure_env_not_found(self, config: Config) -> None:
        with pytest.raises(EnvironmentNotFoundError):
            env.cmd_use(argparse.Namespace(name="env"))
