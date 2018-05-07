# -*- coding: utf-8 -*-
import random
import re

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["stop_task", "delete_service", "delete_cluster",
           "deregister_container_instance"]


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
        res = client.list_services(cluster=cluster, maxResults=10)
        services = res["serviceArns"][:]
        while True:
            next_token = res.get("nextToken")
            if not next_token:
                break

            res = client.list_services(
                cluster=cluster, nextToken=next_token, maxResults=10)
            services.extend(res["serviceArns"])

        if not services:
            raise FailedActivity("No ECS services found")

        # should we filter the number of services to take into account?
        if service_pattern:
            r = re.compile(service_pattern)
            filtered = []
            for service in services:
                if r.search(service):
                    filtered.append(service)
            services = filtered

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
