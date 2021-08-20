import random
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "suspend_processes",
    "resume_processes",
    "stop_random_instances",
    "terminate_random_instances",
    "detach_random_instances",
    "change_subnets",
    "detach_random_volume",
    "attach_volume",
]


def terminate_random_instances(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    instance_count: int = None,
    instance_percent: int = None,
    az: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Terminates one or more random healthy instances associated to an ALB

    A healthy instance is considered one with a status of 'InService'

    Parameters:
            One Of:
                - asg_names: a list of one or more asg names to target
                - tags: a list of key/value pairs to identify the asgs by

            One Of:
                - instance_count: the number of instances to terminate
                - instance_percent: the percentage of instances to terminate
                - az: the availability zone to terminate instances

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if not any([instance_count, instance_percent, az]) or all(
        [instance_percent, instance_count, az]
    ):
        raise FailedActivity(
            'Must specify one of "instance_count", "instance_percent", "az"'
        )

    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    results = []
    for a in asgs["AutoScalingGroups"]:
        # Filter out all instances not currently 'InService'
        instances = [e for e in a["Instances"] if e["LifecycleState"] == "InService"]

        if az:
            instances = [e for e in instances if e["AvailabilityZone"] == az]

            if not instances:
                raise FailedActivity(f"No instances found in Availability Zone: {az}")
        else:
            if instance_percent:
                instance_count = int(
                    float(len(instances) * float(instance_percent)) / 100
                )

            if len(instances) < instance_count:
                raise FailedActivity(
                    "Not enough healthy instances in {} to satisfy "
                    "termination count {} ({})".format(
                        a["AutoScalingGroupName"], instance_count, len(instances)
                    )
                )

            instances = random.sample(instances, instance_count)

        client = aws_client("ec2", configuration, secrets)
        try:
            response = client.terminate_instances(
                InstanceIds=sorted(e["InstanceId"] for e in instances)
            )
            results.append(
                {
                    "AutoScalingGroupName": a["AutoScalingGroupName"],
                    "TerminatingInstances": response["TerminatingInstances"],
                }
            )
        except ClientError as e:
            raise FailedActivity(e.response["Error"]["Message"])
    return results


def stop_random_instances(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    instance_count: int = None,
    instance_percent: int = None,
    az: str = None,
    force: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Terminates one or more random healthy instances associated to an ALB

    A healthy instance is considered one with a status of 'InService'

    Parameters:
        - force: force stop the instances (default: False)

        One Of:
            - asg_names: a list of one or more asg names to target
            - tags: a list of key/value pairs to identify the asgs by

        One Of:
            - instance_count: the number of instances to terminate
            - instance_percent: the percentage of instances to terminate
            - az: the availability zone to terminate instances

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if not any([instance_count, instance_percent, az]) or all(
        [instance_percent, instance_count, az]
    ):
        raise FailedActivity(
            'Must specify one of "instance_count", "instance_percent", "az"'
        )

    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    results = []
    for a in asgs["AutoScalingGroups"]:
        # Filter out all instances not currently 'InService'
        instances = [e for e in a["Instances"] if e["LifecycleState"] == "InService"]

        if az:
            instances = [e for e in instances if e["AvailabilityZone"] == az]

            if not instances:
                raise FailedActivity(f"No instances found in Availability Zone: {az}")
        else:
            if instance_percent:
                instance_count = int(
                    float(len(instances) * float(instance_percent)) / 100
                )

            if len(instances) < instance_count:
                raise FailedActivity(
                    "Not enough healthy instances in %s to satisfy "
                    "stop count %s (%s)"
                    % (a["AutoScalingGroupName"], instance_count, len(instances))
                )

            instances = random.sample(instances, instance_count)

        client = aws_client("ec2", configuration, secrets)
        try:
            response = client.stop_instances(
                InstanceIds=sorted(e["InstanceId"] for e in instances), Force=force
            )
            results.append(
                {
                    "AutoScalingGroupName": a["AutoScalingGroupName"],
                    "StoppingInstances": response["StoppingInstances"],
                }
            )
        except ClientError as e:
            raise FailedActivity(e.response["Error"]["Message"])
    return results


def suspend_processes(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    process_names: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Suspends 1 or more processes on a list of auto scaling groups.

    If no process is specified, all running auto scaling
    processes will be suspended.

    For a list of valid processes that can be suspended, reference:
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html

    Parameters:
        One of:
            - asg_names: a list of one or more asg names to target
            - tags: a list of key/value pairs to identify the asgs by

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if process_names:
        validate_processes(process_names)

    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs["AutoScalingGroups"]:
        params = dict(AutoScalingGroupName=a["AutoScalingGroupName"])
        if process_names:
            params["ScalingProcesses"] = process_names

        logger.debug("Suspending process(es) on {}".format(a["AutoScalingGroupName"]))
        client.suspend_processes(**params)

    return get_asg_by_name(
        [a["AutoScalingGroupName"] for a in asgs["AutoScalingGroups"]], client
    )


def resume_processes(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    process_names: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Resumes 1 or more suspended processes on a list of auto scaling groups.

    If no process is specified, all suspended auto scaling
    processes will be resumed.

    For a list of valid processes that can be suspended, reference:
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html

    Parameters:
        One of:
            - asg_names: a list of one or more asg names to target
            - tags: a list of key/value pairs to identify the asgs by

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if process_names:
        validate_processes(process_names)

    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs["AutoScalingGroups"]:
        params = dict(AutoScalingGroupName=a["AutoScalingGroupName"])
        if process_names:
            params["ScalingProcesses"] = process_names

        logger.debug(
            "Resuming process(es) {} on {}".format(
                process_names, a["AutoScalingGroupName"]
            )
        )
        client.resume_processes(**params)

    return get_asg_by_name(
        [a["AutoScalingGroupName"] for a in asgs["AutoScalingGroups"]], client
    )


def detach_random_instances(
    asg_names: List[str] = None,
    tags: List[dict] = None,
    instance_count: int = None,
    instance_percent: int = None,
    decrement_capacity: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Detaches one or more random instances from an autoscaling group

    Parameters:
        One of:
            asg_names: a list of one or more asg names
            tags: a list of key/value pair to identify asg(s) by

        One of:
            instance_count: integer value of number of instances to detach
            instance_percent: 1-100, percent of instances to detach

        decrement_capacity: boolean value to determine if the desired capacity
        of the autoscaling group should be decreased

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if not any([instance_count, instance_percent]):
        raise FailedActivity(
            'You must specify either "instance_count" or ' '"instance_percent"'
        )

    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    results = {}
    for a in asgs["AutoScalingGroups"]:
        # Filter out all instances not currently 'InService'
        instances = [
            e["InstanceId"]
            for e in a["Instances"]
            if e["LifecycleState"] == "InService"
        ]

        if instance_percent:
            instance_count = int(float(len(instances) * float(instance_percent)) / 100)

        if instance_count > len(instances):
            raise FailedActivity(
                "You are attempting to detach more instances "
                "than exist on asg %s" % (a["AutoScalingGroupName"])
            )

        instances = random.sample(instances, instance_count)
        instances = sorted(instances)

        response = client.detach_instances(
            AutoScalingGroupName=a["AutoScalingGroupName"],
            InstanceIds=instances,
            ShouldDecrementDesiredCapacity=decrement_capacity,
        )
        results.setdefault("Activities", []).extend(response["Activities"])
        results.setdefault("DetachingInstances", []).append(
            {
                "AutoScalingGroupName": a["AutoScalingGroupName"],
                "InstanceIds": instances,
            }
        )
    return results


def change_subnets(
    subnets: List[str],
    asg_names: List[str] = None,
    tags: List[dict] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Adds/removes subnets on autoscaling groups

    Parameters:
        One of:
            asg_names: a list of one or more asg names
            tags: a list of key/value pair to identify asg(s) by

        subnets: a list of subnet IDs to associate to the ASG

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)
    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs["AutoScalingGroups"]:
        client.update_auto_scaling_group(
            AutoScalingGroupName=a["AutoScalingGroupName"],
            VPCZoneIdentifier=",".join(subnets),
        )


def detach_random_volume(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    force: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Detaches a random (non root) ebs volume from ec2 instances
    associated to an ASG

    Parameters:
        One of:
            asg_names: a list of one or more asg names
            tags: a list of key/value pair to identify asg(s) by

        force: force detach volume (default: true)

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)
    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    ec2_client = aws_client("ec2", configuration, secrets)
    results = []
    for a in asgs["AutoScalingGroups"]:
        instances = [e["InstanceId"] for e in a["Instances"]]
        if not instances:
            raise FailedActivity(
                "no instances found for asg: %s" % (a["AutoScalingGroupName"])
            )
        volumes = get_random_instance_volume(ec2_client, instances)

        for v in volumes:
            results.append(
                detach_instance_volume(ec2_client, force, a["AutoScalingGroupName"], v)
            )
    return results


def attach_volume(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Attaches ebs volumes that have been previously detached by CTK

    Parameters:
        One of:
            asg_names: list: one or more asg names
            tags: list: key/value pairs to identify asgs by

    `tags` are expected as a list of dictionary objects:
        [
            {'Key': 'TagKey1', 'Value': 'TagValue1'},
            {'Key': 'TagKey2', 'Value': 'TagValue2'},
            ...
        ]
    """
    validate_asgs(asg_names, tags)
    client = aws_client("autoscaling", configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    ec2_client = aws_client("ec2", configuration, secrets)
    volumes = get_detached_volumes(ec2_client)
    if not volumes:
        raise FailedActivity("No volumes detached by ChaosTookit found")

    results = []
    for volume in volumes:
        for t in volume["Tags"]:
            if t["Key"] != "ChaosToolkitDetached":
                continue
            attach_data = t["Value"].split(";")
            if len(attach_data) != 3:
                continue

            device_name = attach_data[0].split("=")[-1]
            instance_id = attach_data[1].split("=")[-1]
            asg_name = attach_data[2].split("=")[-1]

            if asg_name not in [
                a["AutoScalingGroupName"] for a in asgs["AutoScalingGroups"]
            ]:
                continue
            results.append(
                attach_instance_volume(
                    client, instance_id, volume["VolumeId"], device_name
                )
            )
    return results


###############################################################################
# Private functions
###############################################################################
def validate_asgs(asg_names: List[str] = None, tags: List[Dict[str, str]] = None):
    if not any([asg_names, tags]):
        raise FailedActivity(
            "one of the following arguments are required: asg_names or tags"
        )

    if all([asg_names, tags]):
        raise FailedActivity(
            "only one of the following arguments are allowed: asg_names/tags"
        )


def get_asg_by_name(asg_names: List[str], client: boto3.client) -> AWSResponse:
    logger.debug(f"Searching for ASG(s): {asg_names}.")

    asgs = client.describe_auto_scaling_groups(AutoScalingGroupNames=asg_names)

    if not asgs.get("AutoScalingGroups", []):
        raise FailedActivity(f"Unable to locate ASG(s): {asg_names}")

    found_asgs = [a["AutoScalingGroupName"] for a in asgs["AutoScalingGroups"]]
    invalid_asgs = [a for a in asg_names if a not in found_asgs]
    if invalid_asgs:
        raise FailedActivity(f"No ASG(s) found with name(s): {invalid_asgs}")
    return asgs


def get_asg_by_tags(tags: List[Dict[str, str]], client: boto3.client) -> AWSResponse:
    params = []
    for t in tags:
        params.extend(
            [
                {"Name": "key", "Values": [t["Key"]]},
                {"Name": "value", "Values": [t["Value"]]},
            ]
        )
    paginator = client.get_paginator("describe_tags")
    results = set()
    for p in paginator.paginate(Filters=params):
        for a in p["Tags"]:
            if a["ResourceType"] != "auto-scaling-group":
                continue
            results.add(a["ResourceId"])

    if not results:
        raise FailedActivity(f"No ASG(s) found with matching tag(s): {tags}.")
    return get_asg_by_name(list(results), client)


def get_random_instance_volume(
    client: boto3.client, instance_ids: List[str]
) -> List[Dict[str, str]]:
    results = {}
    try:
        response = client.describe_instances(InstanceIds=instance_ids)["Reservations"]
        for r in response:
            for e in r.get("Instances", []):
                instance_id = e["InstanceId"]
                bdm = e.get("BlockDeviceMappings", [])
                for b in bdm:
                    # skip root devices
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
    except ClientError as e:
        raise FailedActivity(
            "Unable to describe asg instances: %s" % (e.response["Error"]["Message"])
        )


def validate_processes(process_names: List[str]):
    valid_processes = [
        "Launch",
        "Terminate",
        "HealthCheck",
        "AZRebalance",
        "AlarmNotification",
        "ScheduledActions",
        "AddToLoadBalancer",
        "ReplaceUnhealthy",
    ]

    invalid_processes = [p for p in process_names if p not in valid_processes]
    if invalid_processes:
        raise FailedActivity(
            "invalid process(es): {} not in {}.".format(
                invalid_processes, valid_processes
            )
        )


def detach_instance_volume(
    client: boto3.client, force: bool, asg_name: str, volume_data: Dict[str, str]
) -> AWSResponse:
    try:
        response = client.detach_volume(
            Device=volume_data["DeviceName"],
            InstanceId=volume_data["InstanceId"],
            VolumeId=volume_data["VolumeId"],
            Force=force,
        )

        # tag volume with instance information (to reattach on rollback)
        client.create_tags(
            Resources=[volume_data["VolumeId"]],
            Tags=[
                {
                    "Key": "ChaosToolkitDetached",
                    "Value": "DeviceName=%s;InstanceId=%s;ASG=%s"
                    % (volume_data["DeviceName"], volume_data["InstanceId"], asg_name),
                }
            ],
        )
        return response
    except ClientError as e:
        raise FailedActivity(
            "unable to detach volume %s from %s: %s"
            % (
                volume_data["VolumeId"],
                volume_data["InstanceId"],
                e.response["Error"]["Message"],
            )
        )


def get_detached_volumes(
    client: boto3.client, next_token: str = None, results: List[Dict[str, Any]] = None
):
    results = results or []
    params = dict(Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}])
    if next_token:
        params["NextToken"] = next_token
    response = client.describe_volumes(**params)
    results.extend([r for r in response["Volumes"]])
    if response.get("NextToken"):
        get_detached_volumes(response["NextToken"], results)
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
