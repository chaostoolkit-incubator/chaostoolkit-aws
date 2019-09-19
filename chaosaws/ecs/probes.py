# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["service_is_deploying", "are_all_desired_tasks_running",
           "describe_cluster", "describe_service", "describe_tasks"]


def service_is_deploying(cluster: str,
                         service: str,
                         configuration: Configuration = None,
                         secrets: Secrets = None) -> bool:
    """
    Checks to make sure there is not an in progress deployment
    """
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(
        cluster=cluster,
        services=[service]
    )
    if not response['services'] or \
            'deployments' not in response['services'][0]:
        raise FailedActivity('Error retrieving service data from AWS')

    return len(response['services'][0]['deployments']) > 1


def are_all_desired_tasks_running(cluster: str, service: str,
                                  configuration: Configuration = None,
                                  secrets: Secrets = None) -> bool:
    """
    Checks to make sure desired and running tasks counts are equal
    """
    client = aws_client("ecs", configuration, secrets)
    response = client.describe_services(cluster=cluster, services=[service])
    service = response['services'][0]
    return service['desiredCount'] == service['runningCount']


def describe_cluster(cluster: str,
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Returns AWS response describing the specified cluster
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
