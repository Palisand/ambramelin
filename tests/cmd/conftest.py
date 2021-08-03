from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture

from ambramelin.util.config import Config, get_empty_config


@pytest.fixture(autouse=True)
def mock_api(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ambra_sdk.api.Api")


@pytest.fixture(autouse=True)
def config(mocker: MockerFixture, request: SubRequest) -> Config:
    try:
        _config = request.param
    except AttributeError:
        _config = get_empty_config()

    mocker.patch("ambramelin.util.config.load_config", return_value=_config)

    def save_config(config: Config) -> None:
        nonlocal _config
        _config = config

    mocker.patch("ambramelin.util.config.save_config", new=save_config)

    return _config


# TODO: open pytest ticket
#  modeled after https://docs.pytest.org/en/stable/example/simple.html#control-skipping-of-tests-according-to-command-line-option
# def pytest_collection_modifyitems(config, items):
#     for item in items:
#         try:
#             config = next(item.iter_markers(name="config"))
#         except StopIteration:
#             pass
#         else:
#             item.add_marker(
#                 pytest.mark.parametrize("config", config.args, indirect=True)
#             )