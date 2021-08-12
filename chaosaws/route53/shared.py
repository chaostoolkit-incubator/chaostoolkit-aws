import boto3
from botocore.exceptions import ClientError
from logzero import logger

from chaosaws.types import AWSResponse


def hosted_zone_by_id(client: boto3.client, zone_id: str) -> AWSResponse:
    """Shared function for route53 actions/probes that will get a hosted zone

    :param client: A boto3 session client for route53
    :param zone_id: A route53 zone id
    :returns: Dict[str, Any]
    """
    try:
        return client.get_hosted_zone(Id=zone_id)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        return {"HostedZone": []}
