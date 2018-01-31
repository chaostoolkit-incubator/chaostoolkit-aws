# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client

__all__ = ["service_is_deploying"]


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
