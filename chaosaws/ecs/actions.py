# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from chaosaws.types import AWSResponse

import random
from chaosaws import aws_client

__all__ = ["stop_task"]


def stop_task(cluster: str,
              task_id: str,
              reason: str = 'Chaos Testing',
              configuration: Configuration = None,
              secrets: Secrets = None) -> AWSResponse:
    """
    Stop a given ECS task instance
    """
    client = aws_client("ecs", configuration, secrets)
    return client.stop_task(cluster=cluster, task=task_id, reason=reason)


def delete_service(cluster: str,
                   service: str,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Delete a given ECS service
    """
    client = aws_client("ecs", configuration, secrets)
    client.update_service(cluster=cluster, service=service,
                          desiredCount=0,
                          deploymentConfiguration={'maximumPercent': 100,
                                                   'minimumHealthyPercent': 0})
    return client.delete_service(cluster=cluster, service=service)


def delete_random_service(cluster: str,
                          configuration: Configuration = None,
                          secrets: Secrets = None) -> AWSResponse:
    """
    Delete a given ECS service
    """
    client = aws_client("ecs", configuration, secrets)

    res = client.list_services(cluster=cluster, maxResults=10)
    services = res["serviceArns"]
    while "nextToken" in res:
        token = res["nextToken"]
        res = client.list_services(cluster=cluster, nextToken=token,
                                   maxResults=10)
        services.extend(res["serviceArns"])
    x = random.randrange(0, len(services))
    service = services[x].split("/")[1]
    print("The service " + service + " will be deleted.")
    client.update_service(cluster=cluster, service=service,
                          desiredCount=0,
                          deploymentConfiguration={'maximumPercent': 100,
                                                   'minimumHealthyPercent': 0})
    return client.delete_service(cluster=cluster, service=service)


def delete_random_service_filter(cluster: str,
                                 filter: str,
                                 configuration: Configuration = None,
                                 secrets: Secrets = None) -> AWSResponse:
    """
    Delete a given ECS service
    """
    client = aws_client("ecs", configuration, secrets)
    res = client.list_services(cluster=cluster, maxResults=10)
    services = res["serviceArns"]
    while "nextToken" in res:
        token = res["nextToken"]
        res = client.list_services(cluster=cluster, nextToken=token,
                                   maxResults=10)
        services.extend(res["serviceArns"])

    filtered = []
    for service in services:
        if filter in service:
            filtered.append(service)
    if len(filtered) <= 0:
        raise FailedActivity('No service matching the filter: ' + filter)
    x = random.randrange(0, len(filtered))
    service = services[x].split("/")[1]
    print("The service " + service + " will be deleted.")
    client.update_service(cluster=cluster, service=service,
                          desiredCount=0,
                          deploymentConfiguration={'maximumPercent': 100,
                                                   'minimumHealthyPercent': 0})
    return client.delete_service(cluster=cluster, service=service)


def delete_cluster(cluster: str,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Delete a given ECS cluster
    """
    client = aws_client("ecs", configuration, secrets)
    return client.delete_cluster(cluster=cluster)


def deregister_container_instance(cluster: str,
                                  instance_id: str,
                                  force: bool = False,
                                  configuration: Configuration = None,
                                  secrets: Secrets = None) -> AWSResponse:
    """
    Deregister a given ECS container
    """
    client = aws_client("ecs", configuration, secrets)
    return client.deregister_container_instance(cluster=cluster,
                                                containerInstance=instance_id,
                                                force=force)
