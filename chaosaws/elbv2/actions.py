# -*- coding: utf-8 -*-
import random
from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List

import boto3
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

__all__ = ["deregister_target"]


def deregister_target(tg_name: str,
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> AWSResponse:
    """
    Deregisters one random target from target group
    """
    client = aws_client('elbv2', configuration, secrets)
    tg_arn = get_target_group_arns(tg_names=[tg_name], client=client)
    tg_health = get_targets_health_description(tg_arns=tg_arn, client=client)
    random_target = random.choice(tg_health[tg_name]
                                  ['TargetHealthDescriptions'])['Target']['Id']
    logger.debug("Deregistering target {} from target group {}".format(
        random_target, tg_name))

    return client.deregister_targets(TargetGroupArn=tg_arn[tg_name],
                                     Targets=[{'Id': random_target}])

###############################################################################
# Private functions
###############################################################################


def get_target_group_arns(tg_names: List[str],
                          client: boto3.client) -> Dict:
    """
    Return list of target group ARNs based on list of target group names

    return structure:
    {
        "TargetGroupName": "TargetGroupArn",
        ....
    }
    """
    logger.debug("Target group name(s): {} Looking for ARN"
                 .format(str(tg_names)))
    res = client.describe_target_groups(Names=tg_names)
    tg_arns = {}

    for tg in res['TargetGroups']:
        tg_arns[tg['TargetGroupName']] = tg['TargetGroupArn']
    logger.debug("Target groups ARN: {}".format(str(tg_arns)))

    return tg_arns


def get_targets_health_description(tg_arns: Dict,
                                   client: boto3.client) -> Dict:
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
    logger.debug("Target group ARN: {} Getting health descriptions"
                 .format(str(tg_arns)))
    tg_health_descr = {}

    for tg in tg_arns:
        tg_health_descr[tg] = {}
        tg_health_descr[tg]['TargetGroupArn'] = tg_arns[tg]
        tg_health_descr[tg]['TargetHealthDescriptions'] = \
            client.describe_target_health(TargetGroupArn=tg_arns[tg])[
            'TargetHealthDescriptions']
    logger.debug("Health descriptions for target group(s) are: {}"
                 .format(str(tg_health_descr)))

    return tg_health_descr
