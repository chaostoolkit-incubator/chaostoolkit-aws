from typing import List

from chaoslib.types import Configuration, Secrets
from chaoslib.exceptions import FailedActivity

from chaosaws import aws_client, get_logger
from chaosaws.types import AWSResponse

__all__ = ["reboot_msk_broker", "delete_cluster"]

logger = get_logger()


def reboot_msk_broker(
    cluster_arn: str,
    broker_ids: List[str],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Reboot the specified brokers in an MSK cluster.
    """
    client = aws_client("kafka", configuration, secrets)
    logger.debug(
        f"Rebooting MSK brokers: {broker_ids} in cluster {cluster_arn}"
    )
    try:
        return client.reboot_broker(
            ClusterArn=cluster_arn, BrokerIds=broker_ids
        )
    except client.exceptions.NotFoundException:
        raise FailedActivity("The specified cluster was not found")


def delete_cluster(
    cluster_arn: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Delete the given MSK cluster.
    """
    client = aws_client("kafka", configuration, secrets)
    logger.debug(f"Deleting MSK cluster: {cluster_arn}")
    try:
        return client.delete_cluster(ClusterArn=cluster_arn)
    except client.exceptions.NotFoundException:
        raise FailedActivity("The specified cluster was not found")
