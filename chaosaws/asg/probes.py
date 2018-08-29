# -*- coding: utf-8 -*-
from collections import Counter
from typing import Any, Dict, List

import boto3
from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

__all__ = ["desired_equals_healthy", "desired_equals_healthy_tags"]


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
    else:
        raise FailedActivity(
            "No auto-scaling groups matched the tags provided")

    return is_desired_equals_healthy(groups_descr)


###############################################################################
# Private functions
###############################################################################
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
