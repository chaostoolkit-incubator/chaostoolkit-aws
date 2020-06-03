#
import importlib
import time
from typing import Union, Dict, Any
from logzero import logger
import jmespath
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets


def breakup_iterable(values: list, limit: int = 50) -> list:
    for i in range(0, len(values), limit):
        yield values[i:min(i + limit, len(values))]


def jmes_search(json_path: str,
                data: dict,
                value: Union[list, int, bool, str]) -> bool:
    results = jmespath.search(json_path, data)
    if isinstance(value, int) and not isinstance(results, int):
        results = jmespath.search('%s | length(@)' % json_path, data)
    return results == value


def probe_monitor(resource_type: str,
                  probe_name: str,
                  probe_args: Dict[str, Any],
                  disrupted: Any,
                  recovered: Any,
                  json_path: str = None,
                  timeout: int = 300,
                  delay: int = 5,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> Dict[str, Any]:
    def _check_status(_data, _value, _jpath=None):
        if json_path:
            return jmes_search(_jpath, _data, _value)
        return _data == _value

    probes = importlib.import_module('chaosaws.%s.probes' % resource_type)
    if probe_name not in probes.__all__:
        raise FailedActivity('no probe named %s found for %s' % (
            probe_name, resource_type))

    probe_args.update({'configuration': configuration, 'secrets': secrets})
    probe = getattr(probes, probe_name)

    results = {}
    is_disrupted = False
    start_time = time.time()

    while not is_disrupted:
        logger.debug('waiting for disruption to occur')
        if int(time.time() - start_time) > timeout:
            raise FailedActivity('Timeout reached (%s) seconds' % timeout)

        response = probe(**probe_args)
        if _check_status(response, disrupted, json_path):
            is_disrupted = True
            results['ctk:disruption_time'] = time.time()
            continue
        time.sleep(delay)

    is_recovered = False
    while not is_recovered:
        logger.debug('waiting for recovery to occur')
        if int(time.time() - start_time) > timeout:
            raise FailedActivity('Timeout reached (%s) seconds' % timeout)

        response = probe(**probe_args)
        if _check_status(response, recovered, json_path):
            is_recovered = True
            results['ctk:recovery_time'] = time.time()
            continue
        time.sleep(delay)

    results['ctk:monitor_results'] = 'success'
    results['ctk:time_to_recovery'] = int(
        results['ctk:recovery_time'] - results['ctk:disruption_time'])
    results['ctk:monitor_elapsed'] = int(time.time() - start_time)
    return results
