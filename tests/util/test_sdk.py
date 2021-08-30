import pytest
from pytest_mock import MockerFixture

from ambramelin.util import sdk
from ambramelin.util.config import Config, Environment, User
from ambramelin.util.errors import NoEnvironmentSelectedError
from tests.conftest import DummyCredentialManager


class TestGetApi:
    def test_success(
        self, mocker: MockerFixture, dummy_creds_manager: DummyCredentialManager
    ) -> None:
        dummy_creds_manager.set_password("username", "password")
        mocker.patch.object(
            sdk,
            "load_config",
            return_value=Config(
                current="envname",
                envs={"envname": Environment(url="envurl", user="username")},
                users={"username": User(credentials_manager="dummy")},
            ),
        )
        mock_api = mocker.patch.object(sdk, "Api")
        result = sdk.get_api()
        mock_api.assert_called_once_with(
            "envurl", username="username", password="password"
        )
        assert result == mock_api()

    def test_failure_no_env_selected(self, mocker: MockerFixture) -> None:
        mocker.patch.object(
            sdk,
            "load_config",
            return_value=Config(),
        )

        with pytest.raises(NoEnvironmentSelectedError):
            sdk.get_api()
