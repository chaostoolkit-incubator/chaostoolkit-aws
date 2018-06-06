# -*- coding: utf-8 -*-
from typing import Any, Dict

from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["create_cluster", "delete_cluster"]


def create_cluster(name: str, role_arn: str, vpc_config: Dict[str, Any],
                   version: str = None, configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Create a new EKS cluster.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug("Creating EKS cluster: {}".format(name))
    return client.create_cluster(
        name=name, version=version, roleArn=role_arn,
        resourcesVpcConfig=vpc_config)


def delete_cluster(name: str = None, configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Delete the given EKS cluster.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug("Deleting EKS cluster: {}".format(name))
    return client.delete_cluster(name=name)
