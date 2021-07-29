import json
from typing import Union


def pprint_json(j: Union[dict, list]) -> None:
    print(json.dumps(j, indent=2))
