from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "service_is_deploying",
    "are_all_desired_tasks_running",
    "describe_cluster",
    "describe_service",
    "describe_tasks",
]


def service_is_deploying(
    cluster: str,
    service: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """Checks to make sure there is not an in progress deployment"""
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])
    services = response.get("services", [])
    if not services:
        raise FailedActivity("Error retrieving service data from AWS")
    return len(services[0].get("deployments")) > 1


def are_all_desired_tasks_running(
    cluster: str,
    service: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """Checks to make sure desired and running tasks counts are equal"""
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])
    services = response.get("services", [])
    if not services:
        raise FailedActivity("Error retrieving service data from AWS")
    return services[0]["desiredCount"] == services[0]["runningCount"]


def describe_cluster(
    cluster: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
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

    if not response.get("clusters", []):
        raise FailedActivity("Error retrieving information for cluster %s" % (cluster))
    return response


def describe_service(
    cluster: str,
    service: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
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

    if not response.get("services", []):
        raise FailedActivity(
            f"Unable to collect service {cluster} on cluster {service}"
        )
    return response


def describe_tasks(
    cluster: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
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
    paginator = client.get_paginator("list_tasks")
    tasks = []

    for p in paginator.paginate(cluster=cluster):
        for t in p.get("taskArns", []):
            tasks.append(t)

    if not tasks:
        raise FailedActivity("Unable to find any tasks for cluster %s" % (cluster))

    response = client.describe_tasks(cluster=cluster, tasks=tasks)
    return response
