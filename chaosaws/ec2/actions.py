# -*- coding: utf-8 -*-
import random
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List

import boto3
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

__all__ = ["stop_instance", "stop_instances"]


def stop_instance(instance_id: str = None, az: str = None, force: bool = False,
                  filters: List[Dict[str, Any]] = None,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Stop a single EC2 instance.

    You may provide an instance id explicitely or, if you only specify the AZ,
    a random instance will be selected. If you need more control, you can
    also provide a list of filters following the documentation
    https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not az and not instance_id and not filters:
        raise FailedActivity(
            "To stop an EC2 instance, you must specify either the instance id,"
            " an AZ to pick a random instance from, or a set of filters.")

    client = aws_client('ec2', configuration, secrets)

    if not instance_id:
        filters = deepcopy(filters) if filters else []

        if az:
            filters.append({'Name': 'availability-zone', 'Values': [az]})
        instance_types = pick_random_instance(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances in availability zone: {}".format(az))
    else:
        instance_types = get_instance_type_by_id(instance_id, client)

    logger.debug(
        "Picked EC2 instance '{}' from AZ '{}' to be stopped".format(
            instance_types, az))

    return stop_instances_any_type(instance_types=instance_types,
                                   force=force, client=client)


def stop_instances(instance_ids: List[str] = None, az: str = None,
                   filters: List[Dict[str, Any]] = None,

                   force: bool = False, configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Stop the given EC2 instances or, if none is provided, all instances
    of the given availability zone. If you need more control, you can
    also provide a list of filters following the documentation
    https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not az and not instance_ids and not filters:
        raise FailedActivity(
            "To stop EC2 instances, you must specify either the instance ids,"
            " an AZ to pick random instances from, or a set of filters.")

    if az and not instance_ids and not filters:
        logger.warn("""Based on configuration provided I am going to stop all
                    instances in AZ {} !.""".format(az))

    client = aws_client('ec2', configuration, secrets)

    if not instance_ids:
        filters = deepcopy(filters) if filters else []

        if az:
            filters.append({'Name': 'availability-zone', 'Values': [az]})
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances in availability zone: {}".format(az))
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)

    logger.debug(
        "Picked EC2 instances '{}' from AZ '{}' to be stopped".format(
            str(instance_types), az))

    return stop_instances_any_type(instance_types=instance_types,
                                   force=force, client=client)


###############################################################################
# Private functions
###############################################################################
def list_instances_by_type(filters: List[Dict[str, Any]],
                           client: boto3.client) -> List[str]:
    """
    Return all instance ids matching the given filters by type
    (InstanceLifecycle) ie spot, ondemand, etc.
    """
    logger.debug("EC2 instances query: {}".format(str(filters)))
    res = client.describe_instances(Filters=filters)
    logger.debug("Instances matching the filter query: {}".format(str(res)))

    return get_instance_type_from_response(res)


def pick_random_instance(filters: List[Dict[str, Any]],
                         client: boto3.client) -> str:
    """
    Select an instance at random based on the returned list of instances
    matching the given filter.
    """
    instances_type = list_instances_by_type(filters, client)
    random_id = random.choice([item for sublist in instances_type.values()
                               for item in sublist])

    for inst_type in instances_type:
        if random_id in instances_type[inst_type]:
            return {inst_type: [random_id]}


def get_instance_type_from_response(response: Dict) -> Dict:
    """
    Transform list of instance IDs to a dict with IDs by instance type
    """
    instances_type = defaultdict(List)
    # reservations are instances that were started together

    for reservation in response['Reservations']:
        for inst in reservation['Instances']:
            if inst['InstanceLifecycle'] not in instances_type.keys():
                # adding empty list (value) for new instance type (key)
                instances_type[inst['InstanceLifecycle']] = []
            instances_type[inst['InstanceLifecycle']].append(
                inst['InstanceId'])

    return instances_type


def get_spot_request_ids_from_response(response: Dict) -> List[str]:
    """
    Return list of all spot request ids from AWS response object
    (DescribeInstances)
    """
    spot_request_ids = []

    for reservation in response['Reservations']:
        for inst in reservation['Instances']:
            if inst['InstanceLifecycle'] == 'spot':
                spot_request_ids.append(inst['SpotInstanceRequestId'])

    return spot_request_ids


def get_instance_type_by_id(instance_ids: List[str],
                            client: boto3.client) -> Dict:
    """
    Return dict object with instance ids grouped by instance types
    """
    instances_type = defaultdict(List)
    res = client.describe_instances(InstanceIds=instance_ids)

    return get_instance_type_from_response(res)


def stop_instances_any_type(instance_types: dict, force, client: boto3.client):
    """
    Stop instances regardless of the instance type (ondemand, spot)
    """

    if 'normal' in instance_types:
        logger.debug("Stopping instances: {}".format(instance_types['normal']))
        client.stop_instances(InstanceIds=instance_types['normal'],
                              Force=force)

    if 'spot' in instance_types:
        # TODO: proper support for spot fleets
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-fleet.html

        # To properly stop spot instances have to cancel spot requests first
        spot_request_ids = get_spot_request_ids_from_response(
            client.describe_instances(InstanceIds=instance_types['spot']))

        logger.debug("Canceling spot requests: {}".format(spot_request_ids))
        client.cancel_spot_instance_requests(
            SpotInstanceRequestIds=spot_request_ids)
        logger.debug("Terminating spot instances: {}".format(
            instance_types['spot']))
        client.terminate_instances(InstanceIds=instance_types['spot'])

    if 'scheduled' in instance_types:
        # TODO: add support for scheduled inststances
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-scheduled-instances.html

        raise FailedActivity("Scheduled instances support is not implemented")
