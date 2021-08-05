import argparse
import json
import sys
from pathlib import Path

from ambra_sdk.api import Api
from ambra_sdk.service.filtering import Filter, FilterCondition
from ambra_sdk.service.query import QueryOF

from ambramelin.util.errors import InvalidFilterConditionError
from ambramelin.util.input import bool_prompt
from ambramelin.util.output import pprint_json
from ambramelin.util.sdk import get_api


def _get_storage_args(api: Api, uuid: str) -> tuple[str, str, str]:
    """Returns arguments necessary for performing Storage API requests."""
    study = api.Study.get(
        uuid=uuid,
        fields=json.dumps(["engine_fqdn", "storage_namespace", "study_uid"])
    ).get()
    return study["engine_fqdn"], study["storage_namespace"], study["study_uid"]


def _augment_query_with_filters(query: QueryOF, query_filters: list[str]) -> QueryOF:
    for query_filter in query_filters:
        field, cond, val = query_filter.split(".", 2)

        try:
            cond = FilterCondition(cond)
        except ValueError:
            raise InvalidFilterConditionError(cond)

        if cond in {FilterCondition.in_condition, FilterCondition.in_or_null}:
            val = json.dumps(val.split(","))

        query = query.filter_by(Filter(field, FilterCondition(cond), val))

    return query


def cmd_count(args: argparse.Namespace) -> None:
    api = get_api()

    query = api.Study.count()

    if args.filters is not None:
        query = _augment_query_with_filters(query, args.filters)

    print(query.get()["count"])


def cmd_download(args: argparse.Namespace) -> None:
    api = get_api()
    path = Path(args.dest.format(uuid=args.uuid))
    print(f"Downloading study to {path.resolve()}")

    with open(path, mode="wb") as f:
        bytes_downloaded = 0
        for chunk in api.Storage.Study.download(
            *_get_storage_args(api, args.uuid), bundle=args.bundle
        ).iter_content(args.chunk_size):
            f.write(chunk)
            # a progress bar would be nice, but (1) the response does not contain the
            # size of the bundle (no Content-Length header or similar) and (2) a study's
            # 'size', as it exists in a /study/get response, refers to the uncompressed
            # size :(
            bytes_downloaded += len(chunk)
            print(f"{bytes_downloaded:,} bytes downloaded", end="\r")

    print()  # ensure 'bytes downloaded' shown after loop completion


def cmd_get(args: argparse.Namespace) -> None:
    api = get_api()
    pprint_json(
        api.Study.get(
            uuid=args.uuid, fields=args.fields and json.dumps(args.fields)
        ).get()
    )


def cmd_list(args: argparse.Namespace) -> None:
    api = get_api()

    if args.fields is None:
        print("Not specifying 'fields' may produce a lot of output.")

        if not bool_prompt("Do you wish to proceed?"):
            sys.exit(0)

    query = api.Study.list(
        fields=args.fields and json.dumps(args.fields)
    )

    if args.filters is not None:
        query = _augment_query_with_filters(query, args.filters)

    pprint_json(list(query.all()))


def cmd_schema(args: argparse.Namespace) -> None:
    api = get_api()
    pprint_json(
        api.Storage.Study.schema(
            *_get_storage_args(api, args.uuid),
            extended=int(args.extended),
            attachments_only=int(args.attachments_only),
        )
    )
