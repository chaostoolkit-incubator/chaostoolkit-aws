# -*- coding: utf-8 -*-
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["describe_cluster", "list_clusters"]


def describe_cluster(name: str, configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Describe an EKS cluster.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug("Describing EKS cluster: {}".format(name))
    try:
        return client.describe_cluster(name=name)
    except client.exceptions.ResourceNotFoundException:
        return None


def list_clusters(configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    List EKS clusters available to the authenticated account.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug("Listing EKS clusters")
    return client.list_clusters()
