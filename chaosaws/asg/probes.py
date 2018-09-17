# -*- coding: utf-8 -*-
import time
from collections import Counter
from sys import maxsize
from typing import Any, Dict, List

import boto3
from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

__all__ = ["desired_equals_healthy", "desired_equals_healthy_tags",
           "wait_desired_equals_healthy", "wait_desired_equals_healthy_tags",
           "is_scaling_in_progress"]


def desired_equals_healthy(asg_names: List[str],
                           configuration: Configuration = None,
                           secrets: Secrets = None) -> AWSResponse:
    """
    If desired number matches the number of healthy instances

    for each of the auto-scaling groups

    Returns: bool
    """

    if not asg_names:
        raise FailedActivity(
            "Non-empty list of auto scaling groups is required")

    client = aws_client('autoscaling', configuration, secrets)

    groups_descr = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=asg_names)

    return is_desired_equals_healthy(groups_descr)


def desired_equals_healthy_tags(tags: List[Dict[str, str]],
                                configuration: Configuration = None,
                                secrets: Secrets = None) -> AWSResponse:
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
        raise FailedActivity(
            "Non-empty tags is required")

    client = aws_client('autoscaling', configuration, secrets)
    groups_descr = get_asg_by_tags(tags, client)

    return is_desired_equals_healthy(groups_descr)


def wait_desired_equals_healthy(asg_names: List[str],
                                configuration: Configuration = None,
                                timeout: int = 300,
                                secrets: Secrets = None) -> AWSResponse:
    """
    Wait until desired number matches the number of healthy instances

    for each of the auto-scaling groups

    Returns: Boolean, Integer (number of seconds it took to wait)
    """

    if not asg_names:
        raise FailedActivity(
            "Non-empty list of auto scaling groups is required")

    client = aws_client('autoscaling', configuration, secrets)

    start = time.time()

    while True:
        groups_descr = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=asg_names)
        result = is_desired_equals_healthy(groups_descr)

        if (time.time() - start) > timeout:
            logger.debug("Timed out")

            return maxsize

        if result:
            waiting_time = int(time.time() - start)
            logger.debug("Waiting time was: {}".format(waiting_time))

            return waiting_time
        time.sleep(0.1)


def wait_desired_not_equals_healthy_tags(tags: List[Dict[str, str]],
                                         timeout: int = 300,
                                         configuration: Configuration = None,
                                         secrets: Secrets = None
                                         ) -> AWSResponse:
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
        raise FailedActivity(
            "Non-empty tags is required")

    client = aws_client('autoscaling', configuration, secrets)

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
            logger.debug("Waiting time was: {}".format(waiting_time))

            return waiting_time
        time.sleep(0.1)


def wait_desired_equals_healthy_tags(tags: List[Dict[str, str]],
                                     timeout: int = 300,
                                     configuration: Configuration = None,
                                     secrets: Secrets = None) -> AWSResponse:
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
        raise FailedActivity(
            "Non-empty tags is required")

    client = aws_client('autoscaling', configuration, secrets)

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
            logger.debug("Waiting time was: {}".format(waiting_time))

            return waiting_time

        time.sleep(0.1)


def is_scaling_in_progress(tags: List[Dict[str, str]],
                           configuration: Configuration = None,
                           secrets: Secrets = None) -> AWSResponse:
    """
    Check if there is any scaling activity in progress for ASG matching tags

    Returns: Boolean
    """

    if not tags:
        raise FailedActivity(
            "Non-empty tags is required")

    client = aws_client('autoscaling', configuration, secrets)
    groups_descr = get_asg_by_tags(tags, client)

    for group_descr in groups_descr['AutoScalingGroups']:
        for instance in group_descr['Instances']:
            if instance['LifecycleState'] != 'InService' \
                    or instance['HealthStatus'] != 'Healthy':

                logger.debug("Scaling activities in progress: {}".format(True))

                return True

    logger.debug("Scaling activities in progress: {}".format(False))

    return False


###############################################################################
# Private functions
###############################################################################
def get_asg_by_tags(tags: dict, client: boto3.client):

    # The following is needed because AWS API does not support filters
    # on auto-scaling groups

    # fetch all ASGs using paginator
    page_iterator = client.get_paginator(
        'describe_auto_scaling_groups').paginate(
        PaginationConfig={'PageSize': 100})
    asg_descrs = {'AutoScalingGroups': []}

    for page in page_iterator:
        asg_descrs['AutoScalingGroups'].extend(page['AutoScalingGroups'])

    filter_set = set(map(lambda x: "=".join([x['Key'], x['Value']]), tags))

    group_sets = list(map(lambda g: {
        'Name': g['AutoScalingGroupName'],
        'Tags': set(map(
            lambda t: "=".join([t['Key'], t['Value']]), g['Tags'])
        )}, asg_descrs['AutoScalingGroups']))

    filtered_groups = [g['Name']
                       for g in group_sets if filter_set.issubset(g['Tags'])]

    logger.debug("filtered groups: {}".format(filtered_groups))

    if filtered_groups:
        groups_descr = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=filtered_groups)

        return groups_descr
    else:
        raise FailedActivity(
            "No auto-scaling groups matched the tags provided")


def is_desired_equals_healthy(groups_descr: Dict):
    desired_equals_healthy = False

    for group_descr in groups_descr['AutoScalingGroups']:
        healthy_cnt = Counter()

        for instance in group_descr['Instances']:
            if instance['LifecycleState'] == 'InService':
                healthy_cnt[instance['HealthStatus']] += 1

        if healthy_cnt['Healthy']:
            if group_descr['DesiredCapacity'] == healthy_cnt['Healthy']:
                desired_equals_healthy = True
            else:
                desired_equals_healthy = False

                break
        else:
            desired_equals_healthy = False

            break

    return desired_equals_healthy
