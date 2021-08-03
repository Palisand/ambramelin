import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Iterator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from ambra_sdk.service.filtering import FilterCondition, Filter
from pytest_mock import MockerFixture

from ambramelin.cmd.study import cmd_get, cmd_download, cmd_list, cmd_schema


@pytest.fixture(autouse=True)
def mock_api(mocker: MockerFixture) -> MagicMock:
    api = MagicMock()
    mocker.patch("ambramelin.cmd.study.get_api", return_value=api)
    return api


@pytest.fixture(autouse=True)
def mock_pprint_json(mocker: MockerFixture) -> None:
    mocker.patch("ambramelin.cmd.study.pprint_json")


@pytest.fixture(autouse=True)
def mock_get_storage_args(mocker: MockerFixture) -> None:
    mocker.patch(
        "ambramelin.cmd.study._get_storage_args",
        return_value=("engine_fqdn", "storage_namespace", "study_uuid"),
    )


class TestDownload:
    def test_success(self, mock_api: MagicMock):
        uuid = str(uuid4())

        def iter_content(chunk_size: int) -> Iterator[bytes]:
            assert chunk_size == 512
            return iter([b"chunk1", b"chunk2"])

        mock_response = MagicMock()
        mock_response.iter_content = iter_content
        mock_api.Storage.Study.download.return_value = mock_response

        with TemporaryDirectory() as dirname:
            cmd_download(
                argparse.Namespace(
                    dest=f"{dirname}/{{uuid}}.zip",
                    uuid=uuid,
                    bundle="dicom",
                    chunk_size=512,
                )
            )

            mock_api.Storage.Study.download.assert_called_once_with(
                "engine_fqdn", "storage_namespace", "study_uuid", bundle="dicom"
            )

            with open(Path(dirname) / f"{uuid}.zip") as f:
                assert f.read() == "chunk1chunk2"


class TestGet:
    @pytest.mark.parametrize(
        "fields_arg,fields",
        (
            (None, None),
            (["field1", "field2"], '["field1", "field2"]'),
        )
    )
    def test_success(
        self, mock_api: MagicMock, fields_arg: Optional[list[str]], fields: Optional[str]
    ) -> None:
        uuid = str(uuid4())
        cmd_get(argparse.Namespace(uuid=uuid, fields=fields_arg))
        mock_api.Study.get.assert_called_once_with(uuid=uuid, fields=fields)
        mock_api.Study.get().get.assert_called_once_with()


class TestList:
    @pytest.fixture(autouse=True)
    def mock_bool_prompt(self, mocker: MockerFixture) -> None:
        mocker.patch("ambramelin.cmd.study.bool_prompt", return_value=True)

    @pytest.mark.parametrize(
        "fields_arg,fields",
        (
            (None, None),
            (["field1", "field2"], '["field1", "field2"]'),
        )
    )
    @pytest.mark.parametrize(
        "filter_arg,filter",
        (
            (None, None),
            (
                "field.equals.val",
                Filter("field", FilterCondition.equals, "val"),
            ),
            (
                "field.in.val",
                Filter("field", FilterCondition.in_condition, '["val"]'),
            ),
            (
                "field.in.val1,val2",
                Filter("field", FilterCondition.in_condition, '["val1", "val2"]'),
            ),
            (
                "field.in_or_null.val",
                Filter("field", FilterCondition.in_or_null, '["val"]')
            ),
            (
                "field.in_or_null.val1,val2",
                Filter("field", FilterCondition.in_or_null, '["val1", "val2"]')
            ),
        )
    )
    def test_success(
        self,
        mock_api: MagicMock,
        fields_arg: list[str],
        fields: Optional[str],
        filter_arg: Optional[str],
        filter: Filter
    ) -> None:
        cmd_list(argparse.Namespace(fields=fields_arg, filter=filter_arg))

        mock_api.Study.list.assert_called_once_with(fields=fields)

        if filter_arg is not None:
            mock_api.Study.list().filter_by.assert_called_once_with(filter)


class TestSchema:
    @pytest.mark.parametrize("extended", (True, False))
    @pytest.mark.parametrize("attachments_only", (True, False))
    def test_success(self, mock_api: MagicMock, extended: bool, attachments_only: bool):
        uuid = str(uuid4())
        cmd_schema(
            argparse.Namespace(
                uuid=uuid, extended=extended, attachments_only=attachments_only
            )
        )
        mock_api.Storage.Study.schema.assert_called_once_with(
            "engine_fqdn",
            "storage_namespace",
            "study_uuid",
            extended=int(extended),
            attachments_only=int(attachments_only),
        )
