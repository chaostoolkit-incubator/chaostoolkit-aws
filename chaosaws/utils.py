#
import jmespath
from typing import Union


def breakup_iterable(values: list, limit: int = 50) -> list:
    for i in range(0, len(values), limit):
        yield values[i:min(i + limit, len(values))]


def jmes_search(json_path: str,
                data: dict,
                value: Union[list, int, bool, str]) -> bool:
    if isinstance(value, int):
        results = jmespath.search('%s | length(@)' % json_path, data)
    else:
        results = jmespath.search(json_path, data)
    return results == value
