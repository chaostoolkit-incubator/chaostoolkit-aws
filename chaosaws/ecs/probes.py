# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

import time
import sys
from typing import Any, Dict
from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaosaws.utils import jmes_search

here = sys.modules[__name__]
__all__ = ["service_is_deploying", "are_all_desired_tasks_running",
           "monitor", "describe_cluster", "describe_service",
           "describe_tasks"]


def monitor(probe_name: str,
            probe_args: Dict[str, Any],
            disrupted: Any,
            recovered: Any,
            json_path: str = None,
            timeout: int = 300,
            delay: int = 5,
            configuration: Configuration = None,
            secrets: Secrets = None) -> AWSResponse:
    """Monitors for changes to the tasks in an ECS service.
    """
    def _check_status(_data, _value, _jpath=None):
        if json_path:
            return jmes_search(_jpath, _data, _value)
        return _data == _value

    if probe_name not in __all__:
        raise FailedActivity('no probe named %s found for ecs' % probe_name)

    fx = getattr(here, probe_name)
    probe_args.update({'configuration': configuration, 'secrets': secrets})
    is_disrupted = False
    results = {}
    start_time = time.time()

    while not is_disrupted:
        if int(time.time() - start_time) > timeout:
            raise FailedActivity('Timeout reached (%s) seconds' % timeout)

        response = fx(**probe_args)
        if _check_status(response, disrupted, json_path):
            is_disrupted = True
            results['ctk:disruption_time'] = time.time()
            continue
        time.sleep(delay)

    is_recovered = False
    while not is_recovered:
        if int(time.time() - start_time) > timeout:
            raise FailedActivity('Timeout reached (%s) seconds' % timeout)

        response = fx(**probe_args)
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


def service_is_deploying(cluster: str,
                         service: str,
                         configuration: Configuration = None,
                         secrets: Secrets = None) -> bool:
    """Checks to make sure there is not an in progress deployment"""
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])
    services = response.get('services', [])
    if not services:
        raise FailedActivity('Error retrieving service data from AWS')
    return len(services[0].get('deployments')) > 1


def are_all_desired_tasks_running(cluster: str, service: str,
                                  configuration: Configuration = None,
                                  secrets: Secrets = None) -> bool:
    """Checks to make sure desired and running tasks counts are equal"""
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])
    services = response.get('services', [])
    if not services:
        raise FailedActivity('Error retrieving service data from AWS')
    return services[0]['desiredCount'] == services[0]['runningCount']


def describe_cluster(cluster: str,
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Returns AWS response describing the specified cluster

    Probe example:
        "steady-state-hypothesis": {
            "title": "MyCluster has 3 running tasks",
            "probes": [{
                "type": "probe",
                "name": "Cluster running task count",
                "tolerance": {
                    "type": "jsonpath",
                    "path": $.clusters[0].runningTasksCount,
                    "expect": 3
                },
                "provider": {
                    "type": "python",
                    "module": "chaosaws.ecs.probes",
                    "func": "describe_cluster",
                    "arguments": {
                        "cluster": "MyCluster"
                    }
                }
            }
        }

    Full list of possible paths can be found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.describe_clusters
    """
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_clusters(clusters=[cluster])

    if not response.get('clusters', []):
        raise FailedActivity('Error retrieving information for cluster %s' % (
            cluster))
    return response


def describe_service(cluster: str,
                     service: str,
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Returns AWS response describing the specified cluster service

    Probe example:
        "steady-state-hypothesis": {
            "title": "MyService pending count is 1",
            "probes": [{
                "type": "probe",
                "name": "Service pending count",
                "tolerance": {
                    "type": "jsonpath",
                    "path": $.services[0].pendingCount,
                    "expect": 1
                },
                "provider": {
                    "type": "python",
                    "module": "chaosaws.ecs.probes",
                    "func": "describe_service",
                    "arguments": {
                        "cluster": "MyCluster",
                        "service": "MyService"
                    }
                }
            }]
        }

    Full list of possible paths can be found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.describe_services
    """
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])

    if not response.get('services', []):
        raise FailedActivity('Unable to collect service %s on cluster %s' % (
            cluster, service))
    return response


def describe_tasks(cluster: str,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Returns AWS response describing the tasks for a provided cluster

    Probe example:
        "steady-state-hypothesis": {
            "title": "MyCluster tasks are healthy",
            "probes": [{
                "type": "probe",
                "name": "first task is healthy",
                "tolerance": {
                    "type": "jsonpath",
                    "path": $.tasks[0].healthStatus,
                    "expect": "HEALTHY"
                },
                "provider": {
                    "type": "python",
                    "module": "chaosaws.ecs.probes",
                    "func": "describe_tasks",
                    "arguments": {
                        "cluster": "MyCluster"
                    }
                }
            }]
        }

    Full list of possible paths can be found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.describe_tasks
    """
    client = aws_client("ecs", configuration, secrets)
    paginator = client.get_paginator('list_tasks')
    tasks = []

    for p in paginator.paginate(cluster=cluster):
        for t in p.get('taskArns', []):
            tasks.append(t)

    if not tasks:
        raise FailedActivity('Unable to find any tasks for cluster %s' % (
            cluster))

    response = client.describe_tasks(cluster=cluster, tasks=tasks)
    return response
