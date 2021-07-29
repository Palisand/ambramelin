import argparse

from ambramelin.util.config import (
    Config,
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
from ambramelin.util.output import pprint_json


def _check_envs_added_and_env_exists(config: Config, name: str) -> None:
    if not envs_added(config):
        raise NoEnvironmentsError()

    if not env_exists(config, name):
        raise EnvironmentNotFoundError(name, config)


def cmd_add(args: argparse.Namespace) -> None:
    with update_config() as config:

        if env_exists(config, args.name):
            raise EnvironmentAlreadyExistsError(args.name)

        if args.user is not None:
            if not users_added(config):
                raise NoUsersError()

            if not user_exists(config, args.user):
                raise UserNotFoundError(args.user, config)

        config["envs"][args.name] = {"url": args.url, "user": args.user}

    pprint_json({args.name: config["envs"][args.name]})


def cmd_current(_) -> None:
    config = load_config()

    if env_selected(config):
        print(config["current"])
    else:
        print("No environment selected.")


def cmd_del(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        del config["envs"][args.name]

        if config["current"] == args.name:
            config["current"] = None


def cmd_list(_) -> None:
    config = load_config()

    if envs_added(config):
        for name, props in config["envs"].items():
            prefix = "[CURRENT] " if config["current"] == name else ""
            print(f"{prefix}{name}: {props['url']}")
    else:
        print("No environments added.")


def cmd_set(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        if args.url is not None:
            config["envs"][args.name]["url"] = args.url

        if args.user is not None:
            config["envs"][args.name]["user"] = args.user

    pprint_json({args.name: config["envs"][args.name]})


def cmd_use(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_envs_added_and_env_exists(config, args.name)

        config["current"] = args.name
