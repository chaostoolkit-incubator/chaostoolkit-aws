# -*- coding: utf-8 -*-
import random
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Union

import boto3
from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

__all__ = ["stop_instance", "stop_instances", "terminate_instances",
           "terminate_instance"]


def stop_instance(instance_id: str = None, az: str = None, force: bool = False,
                  filters: List[Dict[str, Any]] = None,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Stop a single EC2 instance.

    You may provide an instance id explicitly or, if you only specify the AZ,
    a random instance will be selected. If you need more control, you can
    also provide a list of filters following the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not az and not instance_id and not filters:
        raise FailedActivity(
            "To stop an EC2 instance, you must specify either the instance id,"
            " an AZ to pick a random instance from, or a set of filters.")

    if az and not instance_id and not filters:
        logger.warning('Based on configuration provided I am going to '
                       'stop a random instance in AZ %s!' % az)

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
        instance_types = get_instance_type_by_id([instance_id], client)

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
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not az and not instance_ids and not filters:
        raise FailedActivity(
            "To stop EC2 instances, you must specify either the instance ids,"
            " an AZ to pick random instances from, or a set of filters.")

    if az and not instance_ids and not filters:
        logger.warning('Based on configuration provided I am going to '
                       'stop all instances in AZ %s!' % az)

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


def terminate_instance(instance_id: str = None, az: str = None,
                       filters: List[Dict[str, Any]] = None,
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> List[AWSResponse]:
    """
    Terminates a single EC2 instance.

    An instance may be targeted by specifying it by instance-id. If only the
    availability-zone is provided, a random instances in that AZ will be
    selected and terminated. For more control, please reference the available
    filters found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not any([instance_id, az, filters]):
        raise FailedActivity('To terminate an EC2, you must specify the '
                             'instance-id, an Availability Zone, or provide a '
                             'set of filters')

    if az and not any([instance_id, filters]):
        logger.warning('Based on configuration provided I am going to '
                       'terminate a random instance in AZ %s!' % az)

    client = aws_client('ec2', configuration, secrets)
    if not instance_id:
        filters = deepcopy(filters) or []

        if az:
            filters.append({'Name': 'availability-zone', 'Values': [az]})
            logger.debug('Looking for instances in AZ: %s' % az)

        # Randomly select an instance
        instance_types = pick_random_instance(filters, client)

        if not instance_types:
            raise FailedActivity(
                'No instances found matching filters: %s' % str(filters))

        logger.debug('Instance selected: %s' % str(instance_types))
    else:
        instance_types = get_instance_type_by_id([instance_id], client)

    return terminate_instances_any_type(instance_types, client)


def terminate_instances(instance_ids: List[str] = None, az: str = None,
                        filters: List[Dict[str, Any]] = None,
                        configuration: Configuration = None,
                        secrets: Secrets = None) -> List[AWSResponse]:
    """
    Terminates multiple EC2 instances

    A set of instances may be targeted by providing them as the instance-ids.

    WARNING: If  only an Availability Zone is specified, all instances in
    that AZ will be terminated.

    Additional filters may be used to narrow the scope:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    if not any([instance_ids, az, filters]):
        raise FailedActivity('To terminate instances, you must specify the '
                             'instance-id, an Availability Zone, or provide a '
                             'set of filters')

    if az and not any([instance_ids, filters]):
        logger.warning('Based on configuration provided I am going to '
                       'terminate all instances in AZ %s!' % az)

    client = aws_client('ec2', configuration, secrets)
    if not instance_ids:
        filters = deepcopy(filters) or []

        if az:
            filters.append({'Name': 'availability-zone', 'Values': [az]})
            logger.debug('Looking for instances in AZ: %s' % az)

        # Select instances based on filters
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(
                'No instances found matching filters: %s' % str(filters))

        logger.debug('Instances in AZ %s selected: %s}.' % (
            az, str(instance_types)))
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)

    return terminate_instances_any_type(instance_types, client)


###############################################################################
# Private functions
###############################################################################
def list_instances_by_type(filters: List[Dict[str, Any]],
                           client: boto3.client) -> List[str]:
    """
    Return all instance ids matching the given filters by type
    (InstanceLifecycle) ie spot, on demand, etc.
    """
    logger.debug("EC2 instances query: {}".format(str(filters)))
    res = client.describe_instances(Filters=filters)
    logger.debug("Instances matching the filter query: {}".format(str(res)))

    return get_instance_type_from_response(res)


def pick_random_instance(filters: List[Dict[str, Any]],
                         client: boto3.client) -> Union[str, dict, None]:
    """
    Select an instance at random based on the returned list of instances
    matching the given filter.
    """
    instances_type = list_instances_by_type(filters, client)
    if not instances_type:
        return

    random_id = random.choice([item for sublist in instances_type.values()
                               for item in sublist])

    for k, v in instances_type.items():
        if random_id in v:
            return {k: [random_id]}


def get_instance_type_from_response(response: Dict) -> Dict:
    """
    Transform list of instance IDs to a dict with IDs by instance type
    """
    instances_type = defaultdict(List)
    # reservations are instances that were started together

    for reservation in response['Reservations']:
        for inst in reservation['Instances']:
            # when this field is missing, we assume "normal"
            # which means On-Demand or Reserved
            # this seems what the last line of the docs imply at
            # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html
            lifecycle = inst.get('InstanceLifecycle', 'normal')

            if lifecycle not in instances_type.keys():
                # adding empty list (value) for new instance type (key)
                instances_type[lifecycle] = []

            instances_type[lifecycle].append(
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
            # when this field is missing, we assume "normal"
            # which means On-Demand or Reserved
            lifecycle = inst.get('InstanceLifecycle', 'normal')

            if lifecycle == 'spot':
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


def stop_instances_any_type(instance_types: dict = None,
                            force: bool = False,
                            client: boto3.client = None
                            ) -> List[AWSResponse]:
    """
    Stop instances regardless of the instance type (on demand, spot)
    """

    response = []

    if 'normal' in instance_types:
        logger.debug("Stopping instances: {}".format(instance_types['normal']))

        response.append(
            client.stop_instances(
                InstanceIds=instance_types['normal'],
                Force=force))

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

        response.append(client.terminate_instances(
            InstanceIds=instance_types['spot']))

    if 'scheduled' in instance_types:
        # TODO: add support for scheduled instances
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-scheduled-instances.html

        raise FailedActivity("Scheduled instances support is not implemented")

    return response


def terminate_instances_any_type(instance_types: dict = None,
                                 client: boto3.client = None
                                 ) -> List[AWSResponse]:
    """
    Terminates instance(s) regardless of type
    """
    response = []

    for k, v in instance_types.items():
        logger.debug('Terminating %s instance(s): %s' % (k, instance_types[k]))
        if k == 'spot':
            instances = get_spot_request_ids_from_response(
                client.describe_instances(InstanceIds=v))
            # Cancel spot request prior to termination
            client.cancel_spot_instance_requests(
                SpotInstanceRequestIds=instances)
            response.append(client.terminate_instances(InstanceIds=v))

        response.append(client.terminate_instances(InstanceIds=v))

    return response
