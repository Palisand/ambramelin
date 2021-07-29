import subprocess
from abc import ABC, abstractmethod
from typing import Optional

from ambramelin.util.errors import AmbramelinError


class CredentialManagerError(AmbramelinError):
    pass


class CredentialManager(ABC):

    @abstractmethod
    def get_password(self, account: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_password(self, account: str, password: str) -> None:
        pass

    @abstractmethod
    def del_password(self, account: str) -> None:
        pass

    def password_exists(self, account: str) -> bool:
        if self.get_password(account) is None:
            return False

        return True


class KeychainManager(CredentialManager):
    def get_password(self, account: str) -> Optional[str]:
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
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            return None
        else:
            return res.stdout.decode().strip()

    def set_password(self, account: str, password: str) -> None:
        try:
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
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            raise CredentialManagerError("Failed to set password.") from error

        print(f"Password for '{account}' added to keychain.")

    def del_password(self, account: str) -> None:
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
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            raise CredentialManagerError("Failed to delete password.") from error

        print(f"Password for '{account}' deleted from keychain.")


# TODO: add other managers
#  https://docs.docker.com/engine/reference/commandline/login/#credentials-store
managers = {
    "keychain": KeychainManager(),
}
