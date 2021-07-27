# https://docs.docker.com/engine/reference/commandline/login/#credentials-store
# https://blog.koehntopp.info/2017/01/26/command-line-access-to-the-mac-keychain.html
# https://mostlikelee.com/blog-1/2017/9/16/scripting-the-macos-keychain-partition-ids
import sys
import subprocess
from typing import Optional


def add_keychain_password(account: str, password: str) -> None:
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-a",
            account,
            "-s",
            "ambramelin",
            "-w",
            password,
        ],
        check=True
    )
    print("Password added to keychain under 'ambramelin' service.")


def del_keychain_password(account: str) -> None:
    try:
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-a",
                account,
                "-s",
                "ambramelin",
            ],
            check=True
        )
    except subprocess.CalledProcessError:
        # security program will state the item could not be found
        # TODO: redirect to /dev/null and provide better output
        sys.exit(1)


def keychain_password_exists(account: str) -> bool:
    try:
        subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                "ambramelin",
            ],
            check=True
        )
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def get_keychain_password(account: str) -> Optional[str]:
    try:
        res = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                "ambramelin",
                "-w",
            ],
            check=True,
            stdout=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return None
    else:
        return res.stdout.decode()
