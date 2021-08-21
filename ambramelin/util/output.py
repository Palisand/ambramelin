import json
from typing import Union


# TODO: remove
def pprint_json(j: Union[dict, list]) -> None:
    print(json.dumps(j, indent=2))


MSG_NO_ENV_SELECTED = "No environment selected."
MSG_NO_ENVS_ADDED = "No environments added."
MSG_NO_USER_FOR_CURR_ENV = "No user for current environment ({env})."
MSG_NO_USERS_ADDED = "No users added."
