from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.route53.shared import hosted_zone_by_id
from chaosaws.types import AWSResponse

__all__ = ["get_hosted_zone", "get_health_check_status", "get_dns_answer"]


def get_hosted_zone(
    zone_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """Pull information regarding a specific zone id

    :param zone_id: The route53 zone id
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :returns: Dict[str, Any]
    """
    client = aws_client("route53", configuration, secrets)
    response = hosted_zone_by_id(client, zone_id)
    if not response["HostedZone"]:
        raise FailedActivity("Hosted Zone %s not found." % zone_id)
    return response


def get_health_check_status(
    check_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """Get the status of the specified health check

    :param check_id: The health check id
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :returns: Dict[str, Any]
    """
    client = aws_client("route53", configuration, secrets)
    try:
        response = client.get_health_check_status(HealthCheckId=check_id)
        if not response.get("HealthCheckObservations"):
            raise FailedActivity("No results found for %s" % check_id)
        return response
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def get_dns_answer(
    zone_id: str,
    record_name: str,
    record_type: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Get the DNS response for the specified record name & type

    :param zone_id: The route53 zone id
    :param record_name: The name of the record to get a response for
    :param record_type: The type of the record set
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :returns: Dict[str, Any]
    """
    client = aws_client("route53", configuration, secrets)
    try:
        return client.test_dns_answer(
            HostedZoneId=zone_id, RecordName=record_name, RecordType=record_type
        )
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])
