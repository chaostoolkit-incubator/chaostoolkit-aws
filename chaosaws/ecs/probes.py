# -*- coding: utf-8 -*-
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client

__all__ = ["ecs_service_is_not_deploying"]


def ecs_service_is_not_deploying(cluster: str,
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
    return len(response['services']['deployments']) == 1
