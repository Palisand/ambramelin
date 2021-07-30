import argparse

import pytest

from ambramelin.cmd.env import cmd_add
from ambramelin.util.config import Config
from ambramelin.util.errors import (
    EnvironmentAlreadyExistsError,
    NoUsersError,
    UserNotFoundError,
)


class TestAdd:

    def test_success(self, config: Config) -> None:
        cmd_add(argparse.Namespace(name="envname", url="ambra.com", user=None))
        assert config == {
            "current": None,
            "envs": {"envname": {"url": "ambra.com", "user": None}},
            "users": {},
        }

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"username": {"credential_manager": "keychain"}},
            },
        ),
        indirect=True,
    )
    def test_success_with_user(self, config: Config) -> None:
        cmd_add(argparse.Namespace(name="envname", url="ambra.com", user="username"))
        assert config == {
            "current": None,
            "envs": {"envname": {"url": "ambra.com", "user": "username"}},
            "users": {"username": {"credential_manager": "keychain"}},
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
            cmd_add(argparse.Namespace(name="envname", url="ambra.com", user=None))

    def test_failure_no_users(self) -> None:
        with pytest.raises(NoUsersError):
            cmd_add(argparse.Namespace(
                name="envname", url="ambra.com", user="username")
            )

    @pytest.mark.parametrize(
        "config",
        (
            {
                "current": None,
                "envs": {},
                "users": {"other-username": {"credential_manager": "keychain"}},
            },
        ),
        indirect=True,
    )
    def test_failure_user_not_found(self, config: Config) -> None:
        with pytest.raises(UserNotFoundError):
            cmd_add(
                argparse.Namespace(name="envname", url="ambra.com", user="username")
            )
