from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ambramelin.util import credentials
from ambramelin.util.credentials import CredentialManager


class DummyCredentialManager(CredentialManager):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

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
        new={"dummy": dummy_creds_manager, "mock": mock_creds_manager},
    )
