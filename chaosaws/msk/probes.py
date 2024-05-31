from typing import List

from chaoslib.types import Configuration, Secrets
from chaoslib.exceptions import FailedActivity

from chaosaws import aws_client, get_logger
from chaosaws.types import AWSResponse

__all__ = ["describe_msk_cluster", "get_bootstrap_servers"]

logger = get_logger()


def describe_msk_cluster(
    cluster_arn: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Describe an MSK cluster.
    """
    client = aws_client("kafka", configuration, secrets)
    logger.debug(f"Describing MSK cluster: {cluster_arn}")
    try:
        return client.describe_cluster(ClusterArn=cluster_arn)
    except client.exceptions.NotFoundException:
        raise FailedActivity("The specified cluster was not found")


def get_bootstrap_servers(
    cluster_arn: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[str]:
    """
    Get the bootstrap servers for an MSK cluster.
    """
    client = aws_client("kafka", configuration, secrets)
    logger.debug(f"Getting bootstrap servers for MSK cluster: {cluster_arn}")
    try:
        response = client.get_bootstrap_brokers(ClusterArn=cluster_arn)
        return response["BootstrapBrokerString"].split(",") if response else []
    except client.exceptions.NotFoundException:
        raise FailedActivity("The specified cluster was not found")
