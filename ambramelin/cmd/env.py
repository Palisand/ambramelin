import argparse

import cattr

from ambramelin.util.config import (
    Config,
    Environment,
    load_config,
    envs_added,
    env_exists,
    env_selected,
    update_config,
    users_added,
    user_exists,
)
from ambramelin.util.errors import (
    EnvironmentAlreadyExistsError,
    EnvironmentNotFoundError,
    NoEnvironmentsError,
    NoUsersError,
    UserNotFoundError,
)
from ambramelin.util.output import MSG_NO_ENV_SELECTED, MSG_NO_ENVS_ADDED


def _check_envs_added_and_env_exists(config: Config, name: str) -> None:
    if not envs_added(config):
        raise NoEnvironmentsError()

    if not env_exists(config, name):
        raise EnvironmentNotFoundError(name, config)


def cmd_add(args: argparse.Namespace) -> dict:
    with update_config() as config:

        if env_exists(config, args.name):
            raise EnvironmentAlreadyExistsError(args.name)

        if args.user is not None:
            if not users_added(config):
                raise NoUsersError()

            if not user_exists(config, args.user):
                raise UserNotFoundError(args.user, config)

        config.envs[args.name] = Environment(args.url, args.user)

    return {args.name: cattr.unstructure(config.envs[args.name])}


def cmd_current(_) -> str:
    config = load_config()

    if env_selected(config):
        return config.current
    else:
        return MSG_NO_ENV_SELECTED


def cmd_del(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        del config.envs[args.name]

        if config.current == args.name:
            config.current = None


def cmd_list(_) -> str:
    config = load_config()

    if envs_added(config):
        envs = []

        for name, env in config.envs.items():
            prefix = "[CURRENT] " if config.current == name else ""
            envs.append(f"{prefix}{name}: {env.url}")

        return "\n".join(envs)
    else:
        return MSG_NO_ENVS_ADDED


def cmd_set(args: argparse.Namespace) -> dict:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        if args.url is not None:
            config.envs[args.name].url = args.url

        if args.user is not None:
            if not users_added(config):
                raise NoUsersError()

            if not user_exists(config, args.user):
                raise UserNotFoundError(args.user, config)

            config.envs[args.name].user = args.user

    return {args.name: cattr.unstructure(config.envs[args.name])}


def cmd_use(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        config.current = args.name
