import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Iterator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from ambra_sdk.service.filtering import FilterCondition, Filter
from pytest_mock import MockerFixture

from ambramelin.cmd import study
from ambramelin.util.errors import InvalidFilterConditionError

filter_params = (
    "filters_arg,filters",
    (
        (None, None),
        (
            ["field.equals.val"],
            (Filter("field", FilterCondition.equals, "val"),),
        ),
        (
            ["field.in.val"],
            (Filter("field", FilterCondition.in_condition, '["val"]'),),
        ),
        (
            ["field.in.val1,val2"],
            (Filter("field", FilterCondition.in_condition, '["val1", "val2"]'),),
        ),
        (
            ["field.in_or_null.val"],
            (Filter("field", FilterCondition.in_or_null, '["val"]'),),
        ),
        (
            ["field.in_or_null.val1,val2"],
            (Filter("field", FilterCondition.in_or_null, '["val1", "val2"]'),),
        ),
        (
            ["field.equals.val", "field.in.val1,val2"],
            (
                Filter("field", FilterCondition.equals, "val"),
                Filter("field", FilterCondition.in_or_null, '["val1", "val2"]'),
            ),
        )
    )
)


@pytest.fixture(autouse=True)
def mock_api(mocker: MockerFixture) -> MagicMock:
    api = MagicMock()
    mocker.patch.object(study, "get_api", return_value=api)
    return api


@pytest.fixture(autouse=True)
def mock_get_storage_args(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(
        study,
        "_get_storage_args",
        return_value=("engine_fqdn", "storage_namespace", "study_uuid"),
    )


class TestCount:
    @pytest.mark.parametrize(*filter_params)
    def test_success(
        self,
        mocker: MockerFixture,
        mock_api: MagicMock,
        filters_arg: Optional[tuple[str]],
        filters: list[Filter],
    ):
        if filters_arg is None:
            mock_query_count = MagicMock()
            mock_api.Study.count.return_value = mock_query_count
            mock_query_count.get.return_value = {"count": 0}
        else:
            mock_query = MagicMock()
            mocker.patch.object(
                study, "_augment_query_with_filters", return_value=mock_query
            )
            mock_query.get.return_value = {"count": 1}

        result = study.cmd_count(argparse.Namespace(filters=filters_arg))

        mock_api.Study.count.assert_called_once_with()

        if filters_arg is None:
            assert result == "0"
        else:
            mock_api.Study.count().filter_by.mock_calls = [
                mocker.call(f) for f in filters
            ]
            assert result == "1"

    def test_failure_invalid_filter_condition(self, mocker: MockerFixture) -> None:
        mocker.patch.object(FilterCondition, "__init__", side_effect=ValueError)

        with pytest.raises(InvalidFilterConditionError):
            study.cmd_count(
                argparse.Namespace(fields=None, filters=["field.cond.val"])
            )


class TestDownload:
    def test_success(
        self, mock_api: MagicMock, mock_get_storage_args: MagicMock
    ) -> None:
        uuid = str(uuid4())

        def iter_content(chunk_size: int) -> Iterator[bytes]:
            assert chunk_size == 512
            return iter([b"chunk1", b"chunk2"])

        mock_response = MagicMock()
        mock_response.iter_content = iter_content
        mock_api.Storage.Study.download.return_value = mock_response

        with TemporaryDirectory() as dirname:
            study.cmd_download(
                argparse.Namespace(
                    dest=f"{dirname}/{{uuid}}.zip",
                    uuid=uuid,
                    bundle="dicom",
                    chunk_size=512,
                )
            )

            mock_get_storage_args.assert_called_once_with(mock_api, uuid)
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
        self,
        mock_api: MagicMock,
        fields_arg: Optional[list[str]],
        fields: Optional[str],
    ) -> None:
        uuid = str(uuid4())
        result = study.cmd_get(argparse.Namespace(uuid=uuid, fields=fields_arg))
        mock_api.Study.get.assert_called_once_with(uuid=uuid, fields=fields)
        mock_api.Study.get().get.assert_called_once_with()
        assert result == mock_api.Study.get().get()


class TestList:
    @pytest.fixture(autouse=True)
    def mock_bool_prompt(self, mocker: MockerFixture) -> None:
        mocker.patch.object(study, "bool_prompt", return_value=True)

    @pytest.mark.parametrize(
        "fields_arg,fields",
        (
            (None, None),
            (["field1", "field2"], '["field1", "field2"]'),
        )
    )
    @pytest.mark.parametrize(*filter_params)
    def test_success(
        self,
        mocker: MockerFixture,
        mock_api: MagicMock,
        fields_arg: list[str],
        fields: Optional[str],
        filters_arg: Optional[tuple[str]],
        filters: list[Filter],
    ) -> None:
        if filters_arg is None:
            mock_query_list = MagicMock()
            mock_api.Study.list.return_value = mock_query_list
            mock_query_list.all.return_value = ("unfiltered", "results")
        else:
            mock_query = MagicMock()
            mocker.patch.object(
                study, "_augment_query_with_filters", return_value=mock_query
            )
            mock_query.all.return_value = ("filtered", "results")

        result = study.cmd_list(
            argparse.Namespace(fields=fields_arg, filters=filters_arg)
        )

        mock_api.Study.list.assert_called_once_with(fields=fields)

        if filters_arg is None:
            assert result == ["unfiltered", "results"]
        else:
            mock_api.Study.list().filter_by.mock_calls = [
                mocker.call(f) for f in filters
            ]
            assert result == ["filtered", "results"]

    def test_failure_invalid_filter_condition(self, mocker: MockerFixture) -> None:
        mocker.patch.object(FilterCondition, "__init__", side_effect=ValueError)

        with pytest.raises(InvalidFilterConditionError):
            study.cmd_list(
                argparse.Namespace(fields=None, filters=["field.cond.val"])
            )


class TestSchema:
    @pytest.mark.parametrize("extended", (True, False))
    @pytest.mark.parametrize("attachments_only", (True, False))
    def test_success(
        self,
        mock_api: MagicMock,
        mock_get_storage_args: MagicMock,
        extended: bool,
        attachments_only: bool,
    ) -> None:
        uuid = str(uuid4())
        result = study.cmd_schema(
            argparse.Namespace(
                uuid=uuid, extended=extended, attachments_only=attachments_only
            )
        )
        mock_get_storage_args.assert_called_once_with(mock_api, uuid)
        mock_api.Storage.Study.schema.assert_called_once_with(
            "engine_fqdn",
            "storage_namespace",
            "study_uuid",
            extended=int(extended),
            attachments_only=int(attachments_only),
        )
        assert result == mock_api.Storage.Study.schema()
