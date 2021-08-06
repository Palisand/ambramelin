import json
from typing import Union


# TODO: remove
def pprint_json(j: Union[dict, list]) -> None:
    print(json.dumps(j, indent=2))


MSG_NO_ENV_SELECTED = "No environment selected."
MSG_NO_ENVS_ADDED = "No environments added."
