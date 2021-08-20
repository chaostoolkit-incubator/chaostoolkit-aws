import random
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Union

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import ActivityFailed, FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "stop_instance",
    "stop_instances",
    "terminate_instances",
    "terminate_instance",
    "start_instances",
    "restart_instances",
    "detach_random_volume",
    "attach_volume",
]


def stop_instance(
    instance_id: str = None,
    az: str = None,
    force: bool = False,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
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
            " an AZ to pick a random instance from, or a set of filters."
        )

    if az and not instance_id and not filters:
        logger.warning(
            "Based on configuration provided I am going to "
            "stop a random instance in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)

    if not instance_id:
        filters = deepcopy(filters) if filters else []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
        instance_types = pick_random_instance(filters, client)

        if not instance_types:
            raise FailedActivity(f"No instances in availability zone: {az}")
    else:
        instance_types = get_instance_type_by_id([instance_id], client)

    logger.debug(f"Picked EC2 instance '{instance_types}' from AZ '{az}' to be stopped")

    return stop_instances_any_type(
        instance_types=instance_types, force=force, client=client
    )


def stop_instances(
    instance_ids: List[str] = None,
    az: str = None,
    filters: List[Dict[str, Any]] = None,
    force: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Stop the given EC2 instances or, if none is provided, all instances
    of the given availability zone. If you need more control, you can
    also provide a list of filters following the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not az and not instance_ids and not filters:
        raise FailedActivity(
            "To stop EC2 instances, you must specify either the instance ids,"
            " an AZ to pick random instances from, or a set of filters."
        )

    if az and not instance_ids and not filters:
        logger.warning(
            "Based on configuration provided I am going to "
            "stop all instances in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)

    if not instance_ids:
        filters = deepcopy(filters) if filters else []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(f"No instances in availability zone: {az}")
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)

    logger.debug(
        "Picked EC2 instances '{}' from AZ '{}' to be stopped".format(
            str(instance_types), az
        )
    )

    return stop_instances_any_type(
        instance_types=instance_types, force=force, client=client
    )


def terminate_instance(
    instance_id: str = None,
    az: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Terminates a single EC2 instance.

    An instance may be targeted by specifying it by instance-id. If only the
    availability-zone is provided, a random instances in that AZ will be
    selected and terminated. For more control, please reference the available
    filters found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """

    if not any([instance_id, az, filters]):
        raise FailedActivity(
            "To terminate an EC2, you must specify the "
            "instance-id, an Availability Zone, or provide a "
            "set of filters"
        )

    if az and not any([instance_id, filters]):
        logger.warning(
            "Based on configuration provided I am going to "
            "terminate a random instance in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)
    if not instance_id:
        filters = deepcopy(filters) or []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
            logger.debug("Looking for instances in AZ: %s" % az)

        # Randomly select an instance
        instance_types = pick_random_instance(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances found matching filters: %s" % str(filters)
            )

        logger.debug("Instance selected: %s" % str(instance_types))
    else:
        instance_types = get_instance_type_by_id([instance_id], client)

    return terminate_instances_any_type(instance_types, client)


def terminate_instances(
    instance_ids: List[str] = None,
    az: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Terminates multiple EC2 instances

    A set of instances may be targeted by providing them as the instance-ids.

    WARNING: If  only an Availability Zone is specified, all instances in
    that AZ will be terminated.

    Additional filters may be used to narrow the scope:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    if not any([instance_ids, az, filters]):
        raise FailedActivity(
            "To terminate instances, you must specify the "
            "instance-id, an Availability Zone, or provide a "
            "set of filters"
        )

    if az and not any([instance_ids, filters]):
        logger.warning(
            "Based on configuration provided I am going to "
            "terminate all instances in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)
    if not instance_ids:
        filters = deepcopy(filters) or []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
            logger.debug("Looking for instances in AZ: %s" % az)

        # Select instances based on filters
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances found matching filters: %s" % str(filters)
            )

        logger.debug(f"Instances in AZ {az} selected: {str(instance_types)}}}.")
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)

    return terminate_instances_any_type(instance_types, client)


def start_instances(
    instance_ids: List[str] = None,
    az: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Starts one or more EC2 instances.

    WARNING: If only an Availability Zone is provided, all instances in the
    provided AZ will be started.

    Additional filters may be used to narrow the scope:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    if not any([instance_ids, az, filters]):
        raise FailedActivity(
            "To start instances, you must specify the "
            "instance-id, an Availability Zone, or provide a "
            "set of filters"
        )

    if az and not any([instance_ids, filters]):
        logger.warning(
            "Based on configuration provided I am going to "
            "start all instances in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)

    if not instance_ids:
        filters = deepcopy(filters) or []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
            logger.debug("Looking for instances in AZ: %s" % az)

        # Select instances based on filters
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances found matching filters: %s" % str(filters)
            )

        logger.debug(f"Instances in AZ {az} selected: {str(instance_types)}}}.")
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)
    return start_instances_any_type(instance_types, client)


def restart_instances(
    instance_ids: List[str] = None,
    az: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Restarts one or more EC2 instances.

    WARNING: If only an Availability Zone is provided, all instances in the
    provided AZ will be restarted.

    Additional filters may be used to narrow the scope:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    if not any([instance_ids, az, filters]):
        raise FailedActivity(
            "To restart instances, you must specify the "
            "instance-id, an Availability Zone, or provide a "
            "set of filters"
        )

    if az and not any([instance_ids, filters]):
        logger.warning(
            "Based on configuration provided I am going to "
            "restart all instances in AZ %s!" % az
        )

    client = aws_client("ec2", configuration, secrets)

    if not instance_ids:
        filters = deepcopy(filters) or []

        if az:
            filters.append({"Name": "availability-zone", "Values": [az]})
            logger.debug("Looking for instances in AZ: %s" % az)

        # Select instances based on filters
        instance_types = list_instances_by_type(filters, client)

        if not instance_types:
            raise FailedActivity(
                "No instances found matching filters: %s" % str(filters)
            )

        logger.debug(f"Instances in AZ {az} selected: {str(instance_types)}}}.")
    else:
        instance_types = get_instance_type_by_id(instance_ids, client)
    return restart_instances_any_type(instance_types, client)


def detach_random_volume(
    instance_ids: List[str] = None,
    filters: List[Dict[str, Any]] = None,
    force: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Detaches a random ebs volume (non root) from one or more EC2 instances

    Parameters:
        One of:
            instance_ids: a list of one or more ec2 instance ids
            filters: a list of key/value pairs to pull ec2 instances

        force: force detach volume (default: true)

    Additional filters may be used to narrow the scope:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    """
    if not any([instance_ids, filters]):
        raise FailedActivity(
            "To detach volumes, you must specify the "
            "instance_id or provide a set of filters"
        )

    client = aws_client("ec2", configuration, secrets)

    if not instance_ids:
        filters = deepcopy(filters) or []
        instances = list_instance_volumes(client, filters=filters)
    else:
        instances = list_instance_volumes(client, instance_ids=instance_ids)

    results = []
    for e in instances:
        results.append(detach_instance_volume(client, force, e))
    return results


def attach_volume(
    instance_ids: List[str] = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Attaches a previously detached EBS volume to its associated EC2 instance.

    If neither 'instance_ids' or 'filters' are provided, all detached volumes
    will be reattached to their respective instances

    Parameters:
        One of:
            instance_ids: list: instance ids
            filters: list: key/value pairs to pull ec2 instances
    """
    client = aws_client("ec2", configuration, secrets)

    if not instance_ids and not filters:
        instances = []
    elif not instance_ids and filters:
        filters = deepcopy(filters) or []
        instances = list_instances(client, filters=filters)
    else:
        instances = list_instances(client, instance_ids=instance_ids)

    volumes = get_detached_volumes(client)
    results = []
    for volume in volumes:
        for t in volume["Tags"]:
            if t["Key"] != "ChaosToolkitDetached":
                continue
            attach_data = t["Value"].split(";")
            device_name = attach_data[0].split("=")[-1]
            instance_id = attach_data[1].split("=")[-1]

            if not instances or instance_id in [e["InstanceId"] for e in instances]:
                results.append(
                    attach_instance_volume(
                        client, instance_id, volume["VolumeId"], device_name
                    )
                )
    return results


###############################################################################
# Private functions
###############################################################################
def list_instances_by_type(
    filters: List[Dict[str, Any]], client: boto3.client
) -> Dict[str, Any]:
    """
    Return all instance ids matching the given filters by type
    (InstanceLifecycle) ie spot, on demand, etc.
    """
    logger.debug(f"EC2 instances query: {str(filters)}")
    res = client.describe_instances(Filters=filters)
    logger.debug(f"Instances matching the filter query: {str(res)}")

    return get_instance_type_from_response(res)


def list_instances(
    client: boto3.client,
    filters: List[Dict[str, Any]] = None,
    instance_ids: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return all instance ids matching either the filters or provided list of ids

    Does not group instances by type
    """
    if filters:
        params = dict(Filters=filters)
    else:
        params = dict(InstanceIds=instance_ids)

    results = []
    response = client.describe_instances(**params)["Reservations"]
    for r in response:
        for e in r["Instances"]:
            results.append(e)
    return results


def list_instance_volumes(
    client: boto3.client,
    instance_ids: List[str] = None,
    filters: List[Dict[str, Any]] = None,
) -> List[AWSResponse]:
    """
    Return all (non root) instance volumes for instances matching either
    the provided filters or instance ids (do not group by type)
    """
    if filters:
        params = dict(Filters=filters)
    else:
        params = dict(InstanceIds=instance_ids)

    response = client.describe_instances(**params)["Reservations"]

    if not response:
        raise FailedActivity("no instances found matching: %s" % str(params))

    results = {}
    for r in response:
        for e in r["Instances"]:
            instance_id = e["InstanceId"]
            bdm = e.get("BlockDeviceMappings", [])
            for b in bdm:
                if b["DeviceName"] in ("/dev/sda1", "/dev/xvda"):
                    continue
                results.setdefault(instance_id, []).append(
                    {b["DeviceName"]: b["Ebs"]["VolumeId"]}
                )

    volumes = []
    for r in results:
        # select 1 volume at random
        volume = random.sample(results[r], 1)[0]
        for k, v in volume.items():
            volumes.append({"InstanceId": r, "DeviceName": k, "VolumeId": v})
    return volumes


def pick_random_instance(
    filters: List[Dict[str, Any]], client: boto3.client
) -> Union[str, dict, None]:
    """
    Select an instance at random based on the returned list of instances
    matching the given filter.
    """
    instances_type = list_instances_by_type(filters, client)
    if not instances_type:
        return

    random_id = random.choice(
        [item for sublist in instances_type.values() for item in sublist]
    )

    for k, v in instances_type.items():
        if random_id in v:
            return {k: [random_id]}


def get_instance_type_from_response(response: Dict) -> Dict:
    """
    Transform list of instance IDs to a dict with IDs by instance type
    """
    instances_type = defaultdict(List)
    # reservations are instances that were started together

    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            # when this field is missing, we assume "normal"
            # which means On-Demand or Reserved
            # this seems what the last line of the docs imply at
            # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html
            lifecycle = inst.get("InstanceLifecycle", "normal")

            if lifecycle not in instances_type.keys():
                # adding empty list (value) for new instance type (key)
                instances_type[lifecycle] = []

            instances_type[lifecycle].append(inst["InstanceId"])

    return instances_type


def get_spot_request_ids_from_response(response: Dict) -> List[str]:
    """
    Return list of all spot request ids from AWS response object
    (DescribeInstances)
    """
    spot_request_ids = []

    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            # when this field is missing, we assume "normal"
            # which means On-Demand or Reserved
            lifecycle = inst.get("InstanceLifecycle", "normal")

            if lifecycle == "spot":
                spot_request_ids.append(inst["SpotInstanceRequestId"])

    return spot_request_ids


def get_instance_type_by_id(instance_ids: List[str], client: boto3.client) -> Dict:
    """
    Return dict object with instance ids grouped by instance types
    """
    res = client.describe_instances(InstanceIds=instance_ids)

    return get_instance_type_from_response(res)


def stop_instances_any_type(
    instance_types: dict = None, force: bool = False, client: boto3.client = None
) -> List[AWSResponse]:
    """
    Stop instances regardless of the instance type (on demand, spot)
    """

    response = []
    if "normal" in instance_types:
        logger.debug("Stopping instances: {}".format(instance_types["normal"]))

        response.append(
            client.stop_instances(InstanceIds=instance_types["normal"], Force=force)
        )

    if "spot" in instance_types:
        # TODO: proper support for spot fleets
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-fleet.html

        # To properly stop spot instances have to cancel spot requests first
        spot_request_ids = get_spot_request_ids_from_response(
            client.describe_instances(InstanceIds=instance_types["spot"])
        )

        logger.debug(f"Canceling spot requests: {spot_request_ids}")
        client.cancel_spot_instance_requests(SpotInstanceRequestIds=spot_request_ids)
        logger.debug("Terminating spot instances: {}".format(instance_types["spot"]))

        response.append(client.terminate_instances(InstanceIds=instance_types["spot"]))

    if "scheduled" in instance_types:
        # TODO: add support for scheduled instances
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-scheduled-instances.html
        raise FailedActivity("Scheduled instances support is not implemented")
    return response


def terminate_instances_any_type(
    instance_types: dict = None, client: boto3.client = None
) -> List[AWSResponse]:
    """
    Terminates instance(s) regardless of type
    """
    response = []

    for k, v in instance_types.items():
        logger.debug(f"Terminating {k} instance(s): {instance_types[k]}")
        if k == "spot":
            instances = get_spot_request_ids_from_response(
                client.describe_instances(InstanceIds=v)
            )
            # Cancel spot request prior to termination
            client.cancel_spot_instance_requests(SpotInstanceRequestIds=instances)
            response.append(client.terminate_instances(InstanceIds=v))
            continue
        response.append(client.terminate_instances(InstanceIds=v))
    return response


def start_instances_any_type(
    instance_types: dict, client: boto3.client
) -> List[AWSResponse]:
    """
    Starts one or more instances regardless of type
    """
    results = []
    for k, v in instance_types.items():
        logger.debug(f"Starting {k} instance(s): {v}")
        response = client.start_instances(InstanceIds=v)
        results.extend(response.get("StartingInstances", []))
    return results


def restart_instances_any_type(instance_types: dict, client: boto3.client):
    """
    Restarts one or more instances regardless of type
    """
    results = []
    for k, v in instance_types.items():
        logger.debug(f"Restarting {k} instance(s): {v}")
        client.reboot_instances(InstanceIds=v)
    return results


def detach_instance_volume(
    client: boto3.client, force: bool, volume: Dict[str, str]
) -> AWSResponse:
    """
    Detach volume from an instance
    """
    try:
        response = client.detach_volume(
            Device=volume["DeviceName"],
            InstanceId=volume["InstanceId"],
            VolumeId=volume["VolumeId"],
            Force=force,
        )

        # tag volume with instance information (to reattach on rollback)
        client.create_tags(
            Resources=[volume["VolumeId"]],
            Tags=[
                {
                    "Key": "ChaosToolkitDetached",
                    "Value": "DeviceName=%s;InstanceId=%s"
                    % (volume["DeviceName"], volume["InstanceId"]),
                }
            ],
        )
        return response
    except ClientError as e:
        raise FailedActivity(
            "unable to detach volume %s from %s: %s"
            % (volume["VolumeId"], volume["InstanceId"], e.response["Error"]["Message"])
        )


def get_detached_volumes(client: boto3.client):
    results = []
    paginator = client.get_paginator("describe_volumes")
    for p in paginator.paginate(
        Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}]
    ):
        for v in p["Volumes"]:
            results.append(v)
    return results


def attach_instance_volume(
    client: boto3.client, instance_id: str, volume_id: str, mount_point: str
) -> AWSResponse:
    try:
        response = client.attach_volume(
            Device=mount_point, InstanceId=instance_id, VolumeId=volume_id
        )
        logger.debug(f"Attached volume {volume_id} to instance {instance_id}")
    except ClientError as e:
        raise FailedActivity(
            "Unable to attach volume %s to instance %s: %s"
            % (volume_id, instance_id, e.response["Error"]["Message"])
        )
    return response


def authorize_security_group_ingress(
    requested_security_group_id: str,
    ip_protocol: str,
    from_port: int,
    to_port: int,
    ingress_security_group_id: str = None,
    cidr_ip: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Add one ingress rule to a security group
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_ingress

    - requested_security_group_id: the id for the security group to update
    - ip_protocol: ip protocol name (tcp, udp, icmp, icmpv6) or -1 to specify all
    - from_port: start of port range
    - to_port: end of port range
    - ingress_security_group_id: id of the securiy group to allow access to. You can either specify this or cidr_ip.
    - cidr_ip: the IPv6 CIDR range.
    You can either specify this or ingress_security_group_id
    """  # noqa: E501
    client = aws_client("ec2", configuration, secrets)
    request_kwargs = create_ingress_kwargs(
        requested_security_group_id,
        ip_protocol,
        from_port,
        to_port,
        ingress_security_group_id,
        cidr_ip,
    )
    try:
        response = client.authorize_security_group_ingress(**request_kwargs)
        return response
    except ClientError as e:
        raise ActivityFailed(
            "Failed to add ingress rule: {}".format(e.response["Error"]["Message"])
        )


def revoke_security_group_ingress(
    requested_security_group_id: str,
    ip_protocol: str,
    from_port: int,
    to_port: int,
    ingress_security_group_id: str = None,
    cidr_ip: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Remove one ingress rule from a security group
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.revoke_security_group_ingress

    - requested_security_group_id: the id for the security group to update
    - ip_protocol: ip protocol name (tcp, udp, icmp, icmpv6) or -1 to specify all
    - from_port: start of port range
    - to_port: end of port range
    - ingress_security_group_id: id of the securiy group to allow access to. You can either specify this or cidr_ip.
    - cidr_ip: the IPv6 CIDR range. You can either specify this or ingress_security_group_id
    """  # noqa: E501
    client = aws_client("ec2", configuration, secrets)
    request_kwargs = create_ingress_kwargs(
        requested_security_group_id,
        ip_protocol,
        from_port,
        to_port,
        ingress_security_group_id,
        cidr_ip,
    )
    try:
        response = client.revoke_security_group_ingress(**request_kwargs)
        return response
    except ClientError as e:
        raise ActivityFailed(
            "Failed to remove ingress rule: {}".format(e.response["Error"]["Message"])
        )


def create_ingress_kwargs(
    requested_security_group_id: str,
    ip_protocol: str,
    from_port: int,
    to_port: int,
    ingress_security_group_id: str = None,
    cidr_ip: str = None,
) -> Dict[str, any]:
    request_kwargs = {
        "GroupId": requested_security_group_id,
        "IpPermissions": [
            {
                "IpProtocol": ip_protocol,
                "IpRanges": [
                    {
                        # conditionally assign the following
                        # 'CidrIp': cidr_ip
                    }
                ],
                "FromPort": from_port,
                "ToPort": to_port,
                "UserIdGroupPairs": [
                    {
                        # conditionally assign the following
                        # 'GroupId': ingress_security_group_id
                    }
                ],
            }
        ],
    }
    req = request_kwargs["IpPermissions"][0]
    if cidr_ip is not None:
        req["IpRanges"][0]["CidrIp"] = cidr_ip
    if ingress_security_group_id is not None:
        req["UserIdGroupPairs"][0]["GroupId"] = ingress_security_group_id
    return request_kwargs
