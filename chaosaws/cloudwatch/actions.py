# -*- coding: utf-8 -*-
from typing import Any, Dict, List

import boto3
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from logzero import logger

__all__ = ["delete_rule", "disable_rule", "enable_rule",
           "put_rule", "put_rule_targets", "remove_rule_targets"]


def put_rule(rule_name: str, schedule_expression: str = None,
             event_pattern: str = None, state: str = None,
             description: str = None, role_arn: str = None,
             configuration: Configuration = None,
             secrets: Secrets = None) -> AWSResponse:
    """
    Creates or updates a CloudWatch event rule.

    Please refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#CloudWatchEvents.Client.put_rule
    for details on input arguments.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    kwargs = {
        'Name': rule_name,
    }
    if schedule_expression is not None:
        kwargs['ScheduleExpression'] = schedule_expression
    if event_pattern is not None:
        kwargs['EventPattern'] = event_pattern
    if state is not None:
        kwargs['State'] = state
    if description is not None:
        kwargs['Description'] = description
    if role_arn is not None:
        kwargs['RoleArn'] = role_arn
    return client.put_rule(**kwargs)


def put_rule_targets(rule_name: str, targets: List[Dict[str, Any]],
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Creates or update CloudWatch event rule targets.

    Please refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#CloudWatchEvents.Client.put_targets
    for details on input arguments.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    return client.put_targets(Rule=rule_name, Targets=targets)


def disable_rule(rule_name: str,
                 configuration: Configuration = None,
                 secrets: Secrets = None) -> AWSResponse:
    """
    Disables a CloudWatch rule.
    """
    client = aws_client("events", configuration, secrets)
    return client.disable_rule(Name=rule_name)


def enable_rule(rule_name: str, configuration: Configuration = None,
                secrets: Secrets = None) -> AWSResponse:
    """
    Enables a CloudWatch rule.
    """
    client = aws_client("events", configuration, secrets)
    return client.enable_rule(Name=rule_name)


def delete_rule(rule_name: str, force: bool = False,
                configuration: Configuration = None,
                secrets: Secrets = None) -> AWSResponse:
    """
    Deletes a CloudWatch rule.

    All rule targets must be removed before deleting the rule.
    Set input argument force to True to force all rule targets to be deleted.
    """
    client = aws_client("events", configuration, secrets)
    if force:
        target_ids = _get_rule_target_ids(rule_name, client)
        _remove_rule_targets(rule_name, target_ids, client)
    return client.delete_rule(Name=rule_name)


def remove_rule_targets(rule_name: str, target_ids: List[str] = None,
                        configuration: Configuration = None,
                        secrets: Secrets = None) -> AWSResponse:
    """
    Removes CloudWatch rule targets. If no target ids are provided all targets will be removed.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    if target_ids is None:
        target_ids = _get_rule_target_ids(rule_name, client)
    return _remove_rule_targets(rule_name, target_ids, client)


###############################################################################
# Private functions
###############################################################################
def _remove_rule_targets(rule_name: str, target_ids: str,
                         client: boto3.client):
    """
    Removes provided CloudWatch rule targets.
    """
    logger.debug(
        "Removing {} targets from rule {}: {}".format(
            len(target_ids), rule_name, target_ids)
    )
    return client.remove_targets(Rule=rule_name, Ids=target_ids)


def _get_rule_target_ids(rule_name: str, client: boto3.client,
                         limit: int = None):
    """
    Return all targets for a provided CloudWatch rule name.
    """
    request_kwargs = {
        'Rule': rule_name
    }
    if limit is not None:
        request_kwargs['Limit'] = limit
    targets = []
    while True:
        response = client.list_targets_by_rule(**request_kwargs)
        targets += response['Targets']
        next_token = response.get('NextToken')
        if next_token is None:
            break
        request_kwargs['NextToken'] = next_token
    return [t['Id'] for t in targets]
