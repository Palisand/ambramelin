import argparse
import json
import sys

from getpass import getpass
from ambra_sdk.api import Api
from ambramelin.config import load_config, set_config
from ambramelin.keychain import (
    add_keychain_password,
    del_keychain_password,
    get_keychain_password,
    keychain_password_exists,
)


def get_api():
    config = load_config()

    if config["current"] is None:
        print("No environment selected.")
        sys.exit(1)

    env = config["envs"][config["current"]]
    return Api(
        env["url"], username=env["user"], password=get_keychain_password(env["user"])
    )


# TODO: create modules and submodules per env
def cmd_env(args: argparse.Namespace) -> None:
    config = load_config()
    
    def envs_added() -> bool:
        if config["envs"]:
            return True
        
        print("No environments added.")
        return False
        
    def env_selected() -> bool: 
        if config["current"] is None:
            print("No environment selected.")
            return False
        
        return True
    
    def env_exists(name: str) -> bool:
        if name in config["envs"]:
            return True
        
        print(f"Environment not found. Must be one of {list(config['envs'])}.")
        return False

    if args.env == "add":
        config["envs"][args.name] = {"url": args.url, "user": args.user}

        if args.user is not None:
            if keychain_password_exists(args.user):
                del_keychain_password(args.user)

            add_keychain_password(args.user, getpass())

        set_config(config)

    elif args.env == "del":
        if not envs_added() or not env_exists(args.name):
            sys.exit(1)

        if user := config["envs"][args.name]["user"]:
            del_keychain_password(user)

        del config["envs"][args.name]

        if config["current"] == args.name:
            config["current"] = None

        set_config(config)

    elif args.env == "del-user":
        if not envs_added() or not env_selected():
            sys.exit(1)

        user = config["envs"][config["current"]]["user"]

        if user is None:
            print("No user associated with current environment.")
            sys.exit(1)

        del_keychain_password(user)
        config["envs"][config["current"]]["user"] = None
        set_config(config)

    elif args.env == "list":
        if envs_added():
            for name, props in config["envs"].items():
                prefix = "[CURRENT] " if config["current"] == name else ""
                print(f"{prefix}{name}: {props['url']}")

    # TODO: mult-user support
    elif args.env == "set-user":
        if not envs_added() or not env_selected():
            sys.exit(1)

        if keychain_password_exists(args.username):
            del_keychain_password(args.username)

        add_keychain_password(args.username, getpass())
        config["envs"][config["current"]]["user"] = args.username
        set_config(config)

    elif args.env == "use":
        if not envs_added() or not env_exists(args.name):
            sys.exit(1)

        config["current"] = args.name
        set_config(config)

    else:
        if env_selected():
            print(config["current"])


def cmd_study(args: argparse.Namespace) -> None:
    api = get_api()

    if args.study == "get":
        study = api.Study.get(uuid=args.uuid, fields=json.dumps(args.fields)).get()
        print(json.dumps(study, indent=2))


def cli() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    parser_env = subparsers.add_parser("env")
    parser_env_subparsers = parser_env.add_subparsers(dest="env")
    parser_env_add = parser_env_subparsers.add_parser("add")
    parser_env_add.add_argument("name", type=str)
    parser_env_add.add_argument("url", type=str)
    parser_env_add.add_argument("--user", type=str)
    parser_env_del = parser_env_subparsers.add_parser("del")
    parser_env_del.add_argument("name", type=str)
    parser_env_deluser = parser_env_subparsers.add_parser("del-user")
    parser_env_list = parser_env_subparsers.add_parser("list")
    parser_env_setuser = parser_env_subparsers.add_parser("set-user")
    parser_env_setuser.add_argument("username", type=str)
    parser_env_use = parser_env_subparsers.add_parser("use")
    parser_env_use.add_argument("name", type=str)

    parser_study = subparsers.add_parser("study")
    parser_study_subparsers = parser_study.add_subparsers(dest="study")
    parser_study_get = parser_study_subparsers.add_parser("get")
    parser_study_get.add_argument("uuid", type=str)
    parser_study_get.add_argument("--fields", type=str, nargs="+")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_usage()
    else:
        getattr(sys.modules[__name__], f"cmd_{args.cmd}")(args)
