# -*- coding: utf-8 -*-
import random
import re
from typing import List

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["stop_task", "delete_service", "delete_cluster",
           "deregister_container_instance"]


def stop_task(cluster: str = None, task_id: str = None, service: str = None,
              reason: str = 'Chaos Testing',
              configuration: Configuration = None,
              secrets: Secrets = None) -> AWSResponse:
    """
    Stop a given ECS task instance. If no task_id provided, a random task of
    the given service is stopped.

    You can specify a cluster by its ARN identifier or, if not provided, the
    default cluster will be picked up.
    """
    client = aws_client("ecs", configuration, secrets)
    if not task_id and service:
        tasks = list_tasks(cluster=cluster, service=service, client=client)
        if not tasks:
            raise FailedActivity(
                    "No ECS tasks found for service: {}".format(service))
        task_id = random.choice(tasks)
        task_id = task_id.rsplit("/", 1)[1]

    logger.debug("Stopping ECS task: {}".format(task_id))
    return client.stop_task(cluster=cluster, task=task_id, reason=reason)


def delete_service(service: str = None, cluster: str = None,
                   service_pattern: str = None,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Update a given ECS service by updating it to set the desired count of tasks
    to 0 then delete it. If not provided, a random one will be picked up
    regarding `service_pattern`, if provided, so that only service names
    matching the pattern would be be used. This should be a valid regex.

    You can specify a cluster by its ARN identifier or, if not provided, the
    default cluster will be picked up.
    """
    client = aws_client("ecs", configuration, secrets)
    if not service:
        services = list_services_arns(cluster=cluster, client=client)
        if not services:
            raise FailedActivity(
                "No ECS services found in cluster: {}".format(
                    cluster))

        # should we filter the number of services to take into account?
        if service_pattern:
            services = filter_services(services=services,
                                       pattern=service_pattern)
            if not services:
                raise FailedActivity(
                    "No ECS services matching pattern: {}".format(
                        service_pattern))

        service = random.choice(services)
        service = service.rsplit("/", 1)[1]

    logger.debug("Updating ECS service: {}".format(service))
    client.update_service(cluster=cluster, service=service,
                          desiredCount=0,
                          deploymentConfiguration={
                              'maximumPercent': 100,
                              'minimumHealthyPercent': 0
                          })

    logger.debug("Deleting ECS service: {}".format(service))
    return client.delete_service(cluster=cluster, service=service)


def delete_cluster(cluster: str,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Delete a given ECS cluster
    """
    client = aws_client("ecs", configuration, secrets)
    logger.debug("Deleting ECS cluster: {}".format(cluster))
    return client.delete_cluster(cluster=cluster)


def deregister_container_instance(cluster: str,
                                  instance_id: str,
                                  force: bool = False,
                                  configuration: Configuration = None,
                                  secrets: Secrets = None) -> AWSResponse:
    """
    Deregister a given ECS container. Becareful that tasks handled by this
    instance will remain orphan.
    """
    client = aws_client("ecs", configuration, secrets)
    logger.debug(
        "Deregistering container instance '{}' from ECS cluster: {}".format(
            instance_id, cluster))
    return client.deregister_container_instance(cluster=cluster,
                                                containerInstance=instance_id,
                                                force=force)


###############################################################################
# Private functions
###############################################################################
def list_services_arns(cluster: str, client: boto3.client) -> List[str]:
    """
    Return of all services arns in the given cluster.
    """
    res = client.list_services(cluster=cluster, maxResults=10)
    services = res["serviceArns"][:]
    while True:
        next_token = res.get("nextToken")
        if not next_token:
            break

        res = client.list_services(
            cluster=cluster, nextToken=next_token, maxResults=10)
        services.extend(res["serviceArns"])

    return services


def filter_services(services: List[str], pattern: str) -> List[str]:
    """
    Return the list of services matching the given pattern.
    """
    r = re.compile(pattern)
    return [s for s in services if r.search(s)]


def list_tasks(cluster: str, service: str, client: boto3.client) -> List[str]:
    res = client.list_tasks(cluster=cluster, serviceName=service,
                            maxResults=100)
    tasks = res['taskArns'][:]
    while True:
        next_token = res.get("nextToken")
        if not next_token:
            break

        res = client.list_tasks(cluster=cluster, serviceName=service,
                                nextToken=next_token, maxResults=100)
        tasks.extend(res["taskArns"])
    return tasks
