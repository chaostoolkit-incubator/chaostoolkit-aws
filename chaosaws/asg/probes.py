import time
from collections import Counter
from sys import maxsize
from typing import Any, Dict, List, Union

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaosaws.utils import breakup_iterable

__all__ = [
    "desired_equals_healthy",
    "desired_equals_healthy_tags",
    "wait_desired_equals_healthy",
    "wait_desired_equals_healthy_tags",
    "is_scaling_in_progress",
    "process_is_suspended",
    "has_subnets",
    "describe_auto_scaling_groups",
    "instance_count_by_health",
    "wait_desired_not_equals_healthy_tags",
]


def describe_auto_scaling_groups(
    asg_names: List[str] = None,
    tags: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Returns AWS descriptions for provided ASG(s)

    Params:
        OneOf:
            - asg_names: a list of asg names to describe
            - tags: a list of key/value pairs to collect ASG(s)

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    client = aws_client("autoscaling", configuration, secrets)
    if asg_names:
        return get_asg_by_name(asg_names, client)
    elif tags:
        return get_asg_by_tags(tags, client)
    else:
        raise FailedActivity('Must specify either "asg_names" or "tags"')


def desired_equals_healthy(
    asg_names: List[str], configuration: Configuration = None, secrets: Secrets = None
) -> bool:
    """
    If desired number matches the number of healthy instances
    for each of the auto-scaling groups

    Returns: bool
    """

    if not asg_names:
        raise FailedActivity("Non-empty list of auto scaling groups is required")

    client = aws_client("autoscaling", configuration, secrets)

    groups_descr = client.describe_auto_scaling_groups(AutoScalingGroupNames=asg_names)

    return is_desired_equals_healthy(groups_descr)


def desired_equals_healthy_tags(
    tags: List[Dict[str, str]],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """
    If desired number matches the number of healthy instances

    for each of the auto-scaling groups matching tags provided

    `tags` are  expected as:
    [{
        'Key': 'KeyName',
        'Value': 'KeyValue'
    },
    ...
    ]

    Returns: bool
    """

    if not tags:
        raise FailedActivity("Non-empty tags is required")

    client = aws_client("autoscaling", configuration, secrets)
    groups_descr = get_asg_by_tags(tags, client)

    return is_desired_equals_healthy(groups_descr)


def wait_desired_equals_healthy(
    asg_names: List[str],
    configuration: Configuration = None,
    timeout: Union[int, float] = 300,
    secrets: Secrets = None,
) -> int:
    """
    Wait until desired number matches the number of healthy instances
    for each of the auto-scaling groups

    Returns: Integer (number of seconds it took to wait)
    or sys.maxsize in case of timeout
    """

    if not asg_names:
        raise FailedActivity("Non-empty list of auto scaling groups is required")

    client = aws_client("autoscaling", configuration, secrets)

    start = time.time()

    while True:
        groups_descr = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=asg_names
        )
        result = is_desired_equals_healthy(groups_descr)

        if (time.time() - start) > timeout:
            logger.debug("Timed out")
            return maxsize

        if result:
            waiting_time = int(time.time() - start)
            logger.debug(f"Waiting time was: {waiting_time}")
            return waiting_time
        time.sleep(0.1)


def wait_desired_not_equals_healthy_tags(
    tags: List[Dict[str, str]],
    timeout: Union[int, float] = 300,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """
    Wait until desired number doesn't match the number of healthy instances
    for each of the auto-scaling groups matching tags provided

    `tags` are  expected as:
    [{
        'Key': 'KeyName',
        'Value': 'KeyValue'
    },
    ...
    ]

    Returns: Integer (number of seconds it took to wait)
    or sys.maxsize in case of timeout
    """

    if not tags:
        raise FailedActivity("Non-empty tags is required")

    client = aws_client("autoscaling", configuration, secrets)

    start = time.time()

    while True:
        groups_descr = get_asg_by_tags(tags, client)
        logger.debug(groups_descr)
        result = is_desired_equals_healthy(groups_descr)

        if (time.time() - start) > timeout:
            logger.debug("Timed out")

            return maxsize

        if not result:
            waiting_time = int(time.time() - start)
            logger.debug(f"Waiting time was: {waiting_time}")

            return waiting_time
        time.sleep(0.1)


def wait_desired_equals_healthy_tags(
    tags: List[Dict[str, str]],
    timeout: Union[int, float] = 300,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """
    Wait until desired number matches the number of healthy instances
    for each of the auto-scaling groups matching tags provided

    `tags` are  expected as:
    [{
        'Key': 'KeyName',
        'Value': 'KeyValue'
    },
    ...
    ]

    Returns: Integer (number of seconds it took to wait)
    or sys.maxsize in case of timeout
    """

    if not tags:
        raise FailedActivity("Non-empty tags is required")

    client = aws_client("autoscaling", configuration, secrets)

    start = time.time()

    while True:
        groups_descr = get_asg_by_tags(tags, client)
        logger.debug(groups_descr)
        result = is_desired_equals_healthy(groups_descr)

        if (time.time() - start) > timeout:
            logger.debug("Timed out")

            return maxsize

        if result:
            waiting_time = int(time.time() - start)
            logger.debug(f"Waiting time was: {waiting_time}")

            return waiting_time

        time.sleep(0.1)


def is_scaling_in_progress(
    tags: List[Dict[str, str]],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """
    Check if there is any scaling activity in progress for ASG matching tags

    Returns: Boolean
    """

    if not tags:
        raise FailedActivity("Non-empty tags is required")

    client = aws_client("autoscaling", configuration, secrets)
    groups_descr = get_asg_by_tags(tags, client)

    for group_descr in groups_descr["AutoScalingGroups"]:
        for instance in group_descr["Instances"]:
            if (
                instance["LifecycleState"] != "InService"
                or instance["HealthStatus"] != "Healthy"
            ):

                logger.debug(f"Scaling activities in progress: {True}")
                return True

    logger.debug(f"Scaling activities in progress: {False}")
    return False


def process_is_suspended(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    process_names: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """
    Determines if one or more processes on an ASG are suspended.

    :returns Boolean
    """
    client = aws_client("autoscaling", configuration, secrets)

    if not any([asg_names, tags]):
        raise FailedActivity(
            "one of the following arguments are required: asg_names or tags"
        )

    if all([asg_names, tags]):
        raise FailedActivity(
            "only one of the following arguments are allowed: asg_names/tags"
        )

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs["AutoScalingGroups"]:
        suspended = [p.get("ProcessName") for p in a["SuspendedProcesses"]]
        if not all(p in suspended for p in process_names):
            return False
    return True


def has_subnets(
    subnets: List[str],
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """
    Determines if the provided autoscaling groups are in the provided subnets

    :returns boolean
    """
    client = aws_client("autoscaling", configuration, secrets)

    if not any([asg_names, tags]):
        raise FailedActivity(
            "one of the following arguments are required: asg_names or tags"
        )

    if all([asg_names, tags]):
        raise FailedActivity(
            "only one of the following arguments are allowed: asg_names/tags"
        )

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs["AutoScalingGroups"]:
        if sorted(a["VPCZoneIdentifier"].split(",")) != sorted(subnets):
            return False
    return True


def instance_count_by_health(
    asg_names: List[str] = None,
    tags: List[Dict[str, str]] = None,
    count_healthy: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """Reports the number of instances currently in the ASG by their health
    status

    Params:
        OneOf:
            - asg_names: a list of asg names to describe
            - tags: a list of key/value pairs to collect ASG(s)

        - count_healthy: boolean: true for healthy instance count,
                                  false for unhealthy instance count

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    client = aws_client("autoscaling", configuration, secrets)
    asgs = discover_scaling_groups(client, asg_names, tags)

    status = "Healthy"
    if not count_healthy:
        status = "Unhealthy"

    result = 0
    for a in asgs["AutoScalingGroups"]:
        instances = a["Instances"]
        for instance in instances:
            if instance["HealthStatus"] == status:
                result += 1
    return result


###############################################################################
# Private functions
###############################################################################
def discover_scaling_groups(
    client: boto3.client, asgs: List[str] = None, tags: List[Dict[str, Any]] = None
) -> AWSResponse:
    if not any([asgs, tags]):
        raise FailedActivity(
            "missing one of the required parameters: asg_names or tags"
        )
    if not asgs:
        asgs = []

    if tags:
        tag_filter = []
        for t in tags:
            tag_filter.append({"Name": t["Key"], "Values": [t["Value"]]})
        paginator = client.get_paginator("describe_tags")
        for p in paginator.paginate(Filters=tag_filter):
            asgs.extend(
                [t["ResourceId"] for t in p["Tags"] if t["ResourceId"] not in asgs]
            )

    results = {"AutoScalingGroups": []}
    for group in breakup_iterable(asgs, 50):
        response = client.describe_auto_scaling_groups(AutoScalingGroupNames=group)
        results["AutoScalingGroups"].extend(response["AutoScalingGroups"])
    return results


def get_asg_by_name(asg_names: List[str], client: boto3.client) -> AWSResponse:
    results = {"AutoScalingGroups": []}
    paginator = client.get_paginator("describe_auto_scaling_groups")
    for p in paginator.paginate(AutoScalingGroupNames=asg_names):
        results["AutoScalingGroups"].extend(p["AutoScalingGroups"])

    valid_asgs = [a["AutoScalingGroupName"] for a in results["AutoScalingGroups"]]
    invalid_asgs = [a for a in asg_names if a not in valid_asgs]

    if invalid_asgs:
        raise FailedActivity(f"No ASG(s) found matching: {invalid_asgs}")
    return results


def get_asg_by_tags(
    tags: Union[dict, List[Dict[str, str]]], client: boto3.client
) -> AWSResponse:
    # The following is needed because AWS API does not support filters
    # on auto-scaling groups

    # fetch all ASGs using paginator
    # TODO: simplify this function (similar to actions) & update unit tests
    page_iterator = client.get_paginator("describe_auto_scaling_groups").paginate(
        PaginationConfig={"PageSize": 100}
    )

    asg_descrs = {"AutoScalingGroups": []}

    for page in page_iterator:
        asg_descrs["AutoScalingGroups"].extend(page["AutoScalingGroups"])

    filter_set = set(map(lambda x: "=".join([x["Key"], x["Value"]]), tags))

    group_sets = list(
        map(
            lambda g: {
                "Name": g["AutoScalingGroupName"],
                "Tags": set(map(lambda t: "=".join([t["Key"], t["Value"]]), g["Tags"])),
            },
            asg_descrs["AutoScalingGroups"],
        )
    )

    filtered_groups = [g["Name"] for g in group_sets if filter_set.issubset(g["Tags"])]

    logger.debug(f"filtered groups: {filtered_groups}")

    if filtered_groups:
        groups_descr = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=filtered_groups
        )

        return groups_descr
    else:
        raise FailedActivity("No auto-scaling groups matched the tags provided")


def is_desired_equals_healthy(groups_descr: Dict) -> bool:
    result = False
    for group_descr in groups_descr["AutoScalingGroups"]:
        healthy_cnt = Counter()

        for instance in group_descr["Instances"]:
            if instance["LifecycleState"] == "InService":
                healthy_cnt[instance["HealthStatus"]] += 1

        if (
            healthy_cnt["Healthy"]
            and group_descr["DesiredCapacity"] == healthy_cnt["Healthy"]
        ):
            result = True
            continue

        return False
    return result
