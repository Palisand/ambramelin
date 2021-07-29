import argparse
import json
import sys

from ambra_sdk.api import Api
from ambra_sdk.service.filtering import Filter, FilterCondition

from ambramelin.util.errors import InvalidFilterConditionError
from ambramelin.util.output import pprint_json
from ambramelin.util.sdk import get_api


def _get_storage_args(api: Api, uuid: str) -> tuple[str, str, str]:
    """Returns arguments necessary for performing Storage API requests."""
    study = api.Study.get(
        uuid=uuid,
        fields=json.dumps(["engine_fqdn", "storage_namespace", "study_uid"])
    ).get()
    return study["engine_fqdn"], study["storage_namespace"], study["study_uid"]


def cmd_download(args: argparse.Namespace) -> None:
    api = get_api()

    # TODO: stream to file (see if possible without chunks)
    api.Storage.Study.download(*_get_storage_args(api, args.uuid), bundle=args.bundle)


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

        if input("Do you wish to proceed? [y/n]: ").lower() == "n":
            sys.exit(0)

    query = api.Study.list(
        fields=args.fields and json.dumps(args.fields)
    )

    if args.filter is not None:
        field, cond, val = args.filter.split(".")

        try:
            cond = FilterCondition(cond)
        except ValueError:
            raise InvalidFilterConditionError(cond)

        if cond in {FilterCondition.in_condition, FilterCondition.in_or_null}:
            val = json.dumps(val.split(","))

        query = query.filter_by(Filter(field, FilterCondition(cond), val))

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
