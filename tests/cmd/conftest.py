from unittest.mock import MagicMock

import attr, cattr
import pytest
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture

from ambramelin.util import config as util_config
from ambramelin.util.config import Config
from ambra_sdk import api


@pytest.fixture(autouse=True)
def mock_api(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(api, "Api")


def _copy_config(config: Config) -> Config:
    return cattr.structure(cattr.unstructure(config), Config)


@pytest.fixture(autouse=True)
def config(mocker: MockerFixture, request: SubRequest) -> Config:
    try:
        _config = _copy_config(request.param)
    except AttributeError:
        _config = Config()

    mocker.patch.object(util_config, "load_config", return_value=_copy_config(_config))

    def save_config(config: Config) -> None:
        nonlocal _config
        # apply changes from `config` to `_config`
        for field in attr.fields_dict(Config):
            setattr(_config, field, getattr(config, field))

    mocker.patch.object(util_config, "save_config", new=save_config)

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
