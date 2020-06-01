# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaosaws.utils import probe_monitor

__all__ = ["describe_instances", "count_instances", "instance_state",
           "monitor"]


def monitor(probe_name: str,
            probe_args: Dict[str, Any],
            disrupted: Any,
            recovered: Any,
            json_path: str = None,
            timeout: int = 300,
            delay: int = 5,
            configuration: Configuration = None,
            secrets: Secrets = None) -> AWSResponse:
    """Monitors an existing ASG probe for specific values
    """
    logger.info('Starting monitor of probe "%s"' % probe_name)
    results = probe_monitor('ec2', probe_name, probe_args, disrupted,
                            recovered, json_path, timeout, delay,
                            configuration, secrets)
    return results


def describe_instances(filters: List[Dict[str, Any]],
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> AWSResponse:
    """
    Describe instances following the specified filters.

    Please refer to https://bit.ly/2Sv9lmU

    for details on said filters.
    """  # noqa: E501
    client = aws_client('ec2', configuration, secrets)

    return client.describe_instances(Filters=filters)


def count_instances(filters: List[Dict[str, Any]],
                    configuration: Configuration = None,
                    secrets: Secrets = None) -> int:
    """
    Return count of instances matching the specified filters.

    Please refer to https://bit.ly/2Sv9lmU

    for details on said filters.
    """  # noqa: E501
    client = aws_client('ec2', configuration, secrets)
    result = client.describe_instances(Filters=filters)

    return len(result['Reservations'])


def instance_state(state: str,
                   instance_ids: List[str] = None,
                   filters: List[Dict[str, Any]] = None,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> bool:
    """
    Determines if EC2 instances match desired state

    For additional filter options, please refer to the documentation found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    client = aws_client('ec2', configuration, secrets)

    if not any([instance_ids, filters]):
        raise FailedActivity('Probe "instance_state" missing required '
                             'parameter "instance_ids" or "filters"')

    if instance_ids:
        instances = client.describe_instances(InstanceIds=instance_ids)
    else:
        instances = client.describe_instances(Filters=filters)

    for i in instances['Reservations'][0]['Instances']:
        if i['State']['Name'] != state:
            return False
    return True
