import argparse
import json
import sys
from importlib import import_module

from ambramelin.util import credentials
from ambramelin.util.config import load_config
from ambramelin.util.errors import AmbramelinError


def cli() -> None:
    # TODO: auto-generate documentation
    config = load_config()
    envs = tuple(config.envs) or None
    users = tuple(config.users) or None
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    # env

    parser_env = subparsers.add_parser("env")
    parser_env_subparsers = parser_env.add_subparsers(dest="subcmd")

    parser_env_add = parser_env_subparsers.add_parser("add")
    parser_env_add.add_argument("name", type=str)
    parser_env_add.add_argument("url", type=str)
    parser_env_add.add_argument("--user", type=str, choices=users)

    parser_env_subparsers.add_parser("current")

    parser_env_del = parser_env_subparsers.add_parser("del")
    parser_env_del.add_argument("name", type=str, choices=envs)

    parser_env_subparsers.add_parser("list")

    parser_env_set = parser_env_subparsers.add_parser("set")
    parser_env_set.add_argument("name", type=str, choices=envs)
    parser_env_set.add_argument("--url", type=str)
    parser_env_set.add_argument("--user", type=str, choices=users)

    parser_env_use = parser_env_subparsers.add_parser("use")
    parser_env_use.add_argument("name", type=str, choices=envs)

    # user

    parser_user = subparsers.add_parser("user")
    parser_user_subparsers = parser_user.add_subparsers(dest="subcmd")
    parser_user_add = parser_user_subparsers.add_parser(
        "add", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_user_add.add_argument("name", type=str)
    parser_user_add.add_argument(
        "--creds",
        type=str,
        default="keychain",
        choices=list(credentials.managers),
        help=f"credentials manager",
    )

    parser_user_subparsers.add_parser("current")

    parser_user_del = parser_user_subparsers.add_parser("del")
    parser_user_del.add_argument("name", type=str, choices=users)

    parser_user_subparsers.add_parser("list")

    parser_user_set = parser_user_subparsers.add_parser(
        "set", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_user_set.add_argument("name", type=str, choices=users)
    parser_user_set.add_argument(
        "--creds",
        type=str,
        choices=list(credentials.managers),
        help=f"credentials manager",
    )
    parser_user_set.add_argument("--passwd", action="store_true", help="password")

    # study

    parser_study = subparsers.add_parser("study")
    parser_study_subparsers = parser_study.add_subparsers(dest="subcmd")

    parser_study_count = parser_study_subparsers.add_parser("count")
    parser_study_count.add_argument(
        "filters", type=str, nargs="+", help="field.condition.value"
    )

    parser_study_get = parser_study_subparsers.add_parser("get")
    parser_study_get.add_argument("uuid", type=str)
    parser_study_get.add_argument("--fields", type=str, nargs="+")

    parser_study_download = parser_study_subparsers.add_parser(
        "download", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_study_download.add_argument("uuid", type=str)
    parser_study_download.add_argument(
        "--dest", type=str, default="{uuid}.zip", help="destination"
    )
    parser_study_download.add_argument(
        "--bundle",
        type=str,
        default="dicom",
        choices=["dicom", "iso", "osx", "win"],
        help="bundle type",
    )
    parser_study_download.add_argument(
        "--chunk-size", type=int, default=4096, help="chunk size in bytes"
    )

    parser_study_list = parser_study_subparsers.add_parser("list")
    parser_study_list.add_argument(
        "--filters", type=str, nargs="+", help="field.condition.value"
    )
    parser_study_list.add_argument("--fields", type=str, nargs="+")
    parser_study_list.add_argument("--min-row", type=int)
    parser_study_list.add_argument("--max-row", type=int)

    parser_study_schema = parser_study_subparsers.add_parser("schema")
    parser_study_schema.add_argument("uuid", type=str)
    parser_study_schema.add_argument("--extended", action="store_true")
    parser_study_schema.add_argument("--attachments-only", action="store_true")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_usage()
    elif args.subcmd is None:
        locals()[f"parser_{args.cmd}"].print_usage()
    else:
        try:
            result = getattr(
                import_module(f"ambramelin.cmd.{args.cmd}"), f"cmd_{args.subcmd}"
            )(args)
        except AmbramelinError as e:
            # TODO: option for showing stacktrace (dev mode)
            print(e)
            sys.exit(1)
        else:
            assert result is None or isinstance(
                result, (str, list, dict)
            ), "cmd_* must return a str, list, dict, or None"

            if isinstance(result, str):
                print(result)
            elif isinstance(result, (list, dict)):
                print(json.dumps(result, indent=1))
