import argparse
from getpass import getpass

from ambramelin.util import credentials
from ambramelin.util.config import (
    Config,
    load_config,
    env_selected,
    update_config,
    users_added,
    user_exists,
)
from ambramelin.util.errors import (
    NoUsersError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ambramelin.util.output import (
    MSG_NO_ENV_SELECTED,
    MSG_NO_USERS_ADDED,
    MSG_NO_USER_FOR_CURR_ENV,
)


def _check_users_added_and_user_exists(config: Config, name: str) -> None:
    if not users_added(config):
        raise NoUsersError()

    if not user_exists(config, name):
        raise UserNotFoundError(name, config)


def cmd_add(args: argparse.Namespace) -> dict:
    with update_config() as config:

        if user_exists(config, args.name):
            raise UserAlreadyExistsError(args.name)

        credentials.managers[args.creds].set_password(args.name, getpass())
        config["users"][args.name] = {"credentials_manager": args.creds}

    return {args.name: config["users"][args.name]}


def cmd_current(_) -> str:
    config = load_config()

    if env_selected(config):
        if user := config["envs"][config["current"]]["user"]:
            return user
        else:
            return MSG_NO_USER_FOR_CURR_ENV.format(env=config["current"])
    else:
        return MSG_NO_ENV_SELECTED


def cmd_del(args: argparse.Namespace) -> None:
    with update_config() as config:

        _check_users_added_and_user_exists(config, args.name)

        cred_manager = credentials.managers[
            config["users"][args.name]["credentials_manager"]
        ]
        cred_manager.del_password(args.name)
        del config["users"][args.name]

        for name, props in config["envs"].items():
            if props["user"] == args.name:
                config["envs"][name]["user"] = None


def cmd_list(_) -> str:
    config = load_config()

    if users_added(config):
        users = []

        for name in config["users"]:
            if config["current"] and config["envs"][config["current"]]["user"] == name:
                prefix = "[CURRENT] "
            else:
                prefix = ""

            users.append(f"{prefix}{name}")

        return "\n".join(users)
    else:
        return MSG_NO_USERS_ADDED


def cmd_set(args: argparse.Namespace) -> dict:
    with update_config() as config:

        _check_users_added_and_user_exists(config, args.name)

        if args.creds is not None:
            password = getpass()
            credentials.managers[
                config["users"][args.name]["credentials_manager"]
            ].del_password(args.name)
            credentials.managers[args.creds].set_password(args.name, password)
            config["users"][args.name]["credentials_manager"] = args.creds

        elif args.passwd:
            password = getpass()
            cred_manager = credentials.managers[
                config["users"][args.name]["credentials_manager"]
            ]
            cred_manager.del_password(args.name)
            cred_manager.set_password(args.name, password)

    return {args.name: config["users"][args.name]}
