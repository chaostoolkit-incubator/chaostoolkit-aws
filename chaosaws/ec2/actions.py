# -*- coding: utf-8 -*-
import random
from typing import Any, Dict, List

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse


__all__ = ["stop_instance", "stop_instances"]


def stop_instance(instance_id: str = None, az: str = None, force: bool = False,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Stop a single EC2 instance.

    You may provide an instance id explicitely or, if you only specify the AZ,
    a random instance will be selected.
    """
    if not az and not instance_id:
        raise FailedActivity(
            "To stop an EC2 instance, you must specify an AZ to pick a "
            "random instance from or the instance id to stop")

    client = aws_client('ec2', configuration, secrets)

    if not instance_id:
        filters = [{'Name': 'availability-zone', 'Values': [az]}]
        instance_id = pick_random_instance(filters, client)

        if not instance_id:
            raise FailedActivity(
                "No instances in availability zone: {}".format(az))

    logger.debug(
        "Picked EC2 instance '{}' from AZ '{}' to be stopped".format(
            instance_id, az))

    return client.stop_instances(InstanceIds=[instance_id], Force=force)


def stop_instances(instance_ids: List[str] = None, az: str = None,
                   force: bool = False, configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Stop the given EC2 instances or, if none is provided, all instances
    of the given availability zone.
    """
    if not az and not instance_ids:
        raise FailedActivity(
            "To stop EC2 instances, you must specify the AZ or the list of "
            "instances to stop")

    client = aws_client('ec2', configuration, secrets)

    if not instance_ids:
        filters = [{'Name': 'availability-zone', 'Values': [az]}]
        instance_ids = list_instance_ids(filters, client)

        if not instance_ids:
            raise FailedActivity(
                "No instances in availability zone: {}".format(az))

    logger.debug(
        "Picked EC2 instances '{}' from AZ '{}' to be stopped".format(
            ', '.join(instance_ids), az))

    return client.stop_instances(InstanceIds=instance_ids, Force=force)


###############################################################################
# Private functions
###############################################################################
def list_instance_ids(filters: List[Dict[str, Any]],
                      client: boto3.client) -> List[str]:
    """
    Return of all instance ids matching the given filters.
    """
    res = client.describe_instances(Filters=filters)
    instance_ids = []

    # reservations are instances that were started together
    for reservation in res['Reservations']:
        for inst in reservation['Instances']:
            instance_ids.append(inst['InstanceId'])

    return instance_ids


def pick_random_instance(filters: List[Dict[str, Any]],
                         client: boto3.client) -> str:
    """
    Select an instance at random based on the returned list of instances
    matching the given filter.
    """
    instance_ids = list_instance_ids(filters, client)
    return random.choice(instance_ids)
