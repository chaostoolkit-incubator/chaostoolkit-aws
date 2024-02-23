from typing import Any, Dict

from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client, get_logger
from chaosaws.types import AWSResponse

__all__ = ["create_cluster", "delete_cluster"]

logger = get_logger()


def create_cluster(
    name: str,
    role_arn: str,
    vpc_config: Dict[str, Any],
    version: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Create a new EKS cluster.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug(f"Creating EKS cluster: {name}")
    return client.create_cluster(
        name=name,
        version=version,
        roleArn=role_arn,
        resourcesVpcConfig=vpc_config,
    )


def delete_cluster(
    name: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Delete the given EKS cluster.
    """
    client = aws_client("eks", configuration, secrets)
    logger.debug(f"Deleting EKS cluster: {name}")
    return client.delete_cluster(name=name)
