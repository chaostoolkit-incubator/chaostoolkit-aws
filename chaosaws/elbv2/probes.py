from collections import Counter
from typing import Dict, List

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["targets_health_count", "all_targets_healthy"]


def targets_health_count(
    tg_names: List[str], configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Count of healthy/unhealthy targets per targetgroup
    """

    if not tg_names:
        raise FailedActivity("Non-empty list of target groups is required")

    client = aws_client("elbv2", configuration, secrets)

    return get_targets_health_count(tg_names=tg_names, client=client)


def all_targets_healthy(
    tg_names: List[str], configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Return true/false based on if all targets for listed
    target groups are healthy
    """

    if not tg_names:
        raise FailedActivity("Non-empty list of target groups is required")

    client = aws_client("elbv2", configuration, secrets)
    logger.debug(f"Checking if all targets are healthy for targets: {str(tg_names)}")
    tg_arns = get_target_group_arns(tg_names=tg_names, client=client)
    tg_health = get_targets_health_description(tg_arns=tg_arns, client=client)
    result = True

    for tg in tg_health:
        time_to_break = False

        for health_descr in tg_health[tg]["TargetHealthDescriptions"]:
            if health_descr["TargetHealth"]["State"] != "healthy":
                result = False
                time_to_break = True

                break

        if time_to_break:
            break

    return result


###############################################################################
# Private functions
###############################################################################
def get_target_group_arns(tg_names: List[str], client: boto3.client) -> Dict:
    """
    Return list of target group ARNs based on list of target group names

    return structure:
    {
        "TargetGroupName": "TargetGroupArn",
        ....
    }
    """
    logger.debug(f"Target group name(s): {str(tg_names)} Looking for ARN")
    res = client.describe_target_groups(Names=tg_names)
    tg_arns = {}

    for tg in res["TargetGroups"]:
        tg_arns[tg["TargetGroupName"]] = tg["TargetGroupArn"]
    logger.debug(f"Target groups ARNs: {str(tg_arns)}")

    return tg_arns


def get_targets_health_description(tg_arns: Dict, client: boto3.client) -> Dict:
    """
    Return TargetHealthDescriptions by targetgroups
    Structure:
    {
        "TargetGroupName": {
            "TargetGroupArn": value,
            "TargetHealthDescriptions": TargetHealthDescriptions[]
        },
        ....
    }
    """
    logger.debug(f"Target group ARN: {str(tg_arns)} Getting health descriptions")
    tg_health_descr = {}

    for tg in tg_arns:
        tg_health_descr[tg] = {}
        tg_health_descr[tg]["TargetGroupArn"] = tg_arns[tg]
        tg_health_descr[tg]["TargetHealthDescriptions"] = client.describe_target_health(
            TargetGroupArn=tg_arns[tg]
        )["TargetHealthDescriptions"]
    logger.debug(f"Health descriptions for target group(s) are: {str(tg_health_descr)}")

    return tg_health_descr


def get_targets_health_count(tg_names: List[str], client: boto3.client) -> Dict:
    """
    Return number of healthy/unhealthy targets per target group
    Structure:
    {
        "TargetGroupName": {
            "healthy": 3,
            "unhealthy": 1
        },
        ....
    }
    """
    logger.debug(
        "Looking for number of health targets for targetgroups: {}".format(
            str(tg_names)
        )
    )
    tg_arns = get_target_group_arns(tg_names=tg_names, client=client)
    tg_health = get_targets_health_description(tg_arns=tg_arns, client=client)
    tg_targets_health_count = {}

    for tg in tg_health:
        cnt = Counter()

        for health_descr in tg_health[tg]["TargetHealthDescriptions"]:
            cnt[health_descr["TargetHealth"]["State"]] += 1
        tg_targets_health_count[tg] = dict(cnt)
    logger.debug(f"Healthy targets by targetgroup: {str(tg_targets_health_count)}")

    return tg_targets_health_count
