from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["associate_vpc_with_zone", "disassociate_vpc_from_zone"]


def associate_vpc_with_zone(
    zone_id: str,
    vpc_id: str,
    vpc_region: str,
    comment: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Associate a VPC with a private hosted zone

    :param zone_id: The hosted zone id
    :param vpc_id: The id of the vpc
    :param vpc_region: The region of the vpc
    :param configuration: access values used by actions/probes
    :param comment: a comment regarding the request
    :param secrets: values that need to be passed on to actions/probes
    :returns: Dict[str, Any]
    """
    client = aws_client("route53", configuration, secrets)
    params = {
        "HostedZoneId": zone_id,
        "VPC": {"VPCId": vpc_id, "VPCRegion": vpc_region},
        **({"Comment": comment} if comment else {}),
    }
    try:
        return client.associate_vpc_with_hosted_zone(**params)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def disassociate_vpc_from_zone(
    zone_id: str,
    vpc_id: str,
    vpc_region: str,
    comment: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Remove an association between a VPC and a private hosted zone

    :param zone_id: The hosted zone id
    :param vpc_id: The id of the vpc
    :param vpc_region: The region of the vpc
    :param comment: A note regarding the disassociation request
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :returns: Dict[str, Any]
    """
    client = aws_client("route53", configuration, secrets)
    params = {
        "HostedZoneId": zone_id,
        "VPC": {"VPCId": vpc_id, "VPCRegion": vpc_region},
        **({"Comment": comment} if comment else {}),
    }
    try:
        return client.disassociate_vpc_from_hosted_zone(**params)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])
