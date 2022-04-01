from datetime import datetime, timedelta
from time import sleep
from typing import Any, Dict, List, Union

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "delete_rule",
    "disable_rule",
    "enable_rule",
    "put_metric_data",
    "put_rule",
    "put_rule_targets",
    "remove_rule_targets",
    "put_metric_data_incremental",
]


def put_rule(
    rule_name: str,
    schedule_expression: str = None,
    event_pattern: str = None,
    state: str = None,
    description: str = None,
    role_arn: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Creates or updates a CloudWatch event rule.

    Please refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#CloudWatchEvents.Client.put_rule
    for details on input arguments.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    kwargs = {
        "Name": rule_name,
        **({"ScheduleExpression": schedule_expression} if schedule_expression else {}),
        **({"EventPattern": event_pattern} if event_pattern else {}),
        **({"State": state} if state else {}),
        **({"Description": description} if description else {}),
        **({"RoleArn": role_arn} if role_arn else {}),
    }
    return client.put_rule(**kwargs)


def put_rule_targets(
    rule_name: str,
    targets: List[Dict[str, Any]],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Creates or update CloudWatch event rule targets.

    Please refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#CloudWatchEvents.Client.put_targets
    for details on input arguments.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    return client.put_targets(Rule=rule_name, Targets=targets)


def disable_rule(
    rule_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Disables a CloudWatch rule.
    """
    client = aws_client("events", configuration, secrets)
    return client.disable_rule(Name=rule_name)


def enable_rule(
    rule_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Enables a CloudWatch rule.
    """
    client = aws_client("events", configuration, secrets)
    return client.enable_rule(Name=rule_name)


def delete_rule(
    rule_name: str,
    force: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
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


def remove_rule_targets(
    rule_name: str,
    target_ids: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Removes CloudWatch rule targets. If no target ids are provided all targets will be removed.
    """  # noqa: E501
    client = aws_client("events", configuration, secrets)
    if target_ids is None:
        target_ids = _get_rule_target_ids(rule_name, client)
    return _remove_rule_targets(rule_name, target_ids, client)


def put_metric_data(
    namespace: str,
    metric_data: List[Dict[str, Any]],
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Publish metric data points to CloudWatch

    :param namespace: The metric namespace
    :param metric_data: A list of metric data to submit
    :param configuration: AWS authentication configuration
    :param secrets: Additional authentication secrets
    :return: None

    example:
        namespace='MyCustomTestMetric',
        metric_data=[
            {
                'MetricName': 'MemoryUsagePercent',
                'Dimensions': [
                    {'Name': 'InstanceId', 'Value': 'i-000000000000'},
                    {'Name': 'Instance Name', 'Value': 'Test Instance'}
                ],
                'Timestamp': datetime(yyyy, mm, dd, HH, MM, SS),
                'Value': 55.55,
                'Unit': 'Percent',
                'StorageResolution': 60
            }
        ]

    For additional information, consult: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
    """  # noqa: E501
    params = {"Namespace": namespace, "MetricData": metric_data}

    client = aws_client("cloudwatch", configuration, secrets)

    try:
        client.put_metric_data(**params)
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])


def put_metric_data_incremental(
    namespace: str,
    metric_name: str,
    dimensions: List[Dict[str, Any]],
    metric_value: float,
    metric_unit: str,
    duration: int = 300,
    increment: float = 0.0,
    storage_resolution: int = 60,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Publish metric data to Cloudwatch over a period of time

    :param namespace: The metric namespace
    :param metric_name: The name of the metric
    :param dimensions: The dimensions associated with the metric
    :param metric_value: The value for the metric
    :param metric_unit: The unit to use when storing the metric
    :param duration: The amount of time (in seconds) over which the data will be added
    :param increment: The amount the data count will increment each put
    :param storage_resolution: Resolution value of the metric (1 = high-resolution)
    :param configuration: AWS authentication configuration
    :param secrets: Additional authentication secrets
    :return: None

    Additional Info: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
    """  # noqa: E501
    put_data_end = datetime.now() + timedelta(seconds=duration)
    while datetime.now() < put_data_end:
        metric_data = [
            {
                "MetricName": metric_name,
                "Dimensions": dimensions,
                "Value": metric_value,
                "Unit": metric_unit,
                "StorageResolution": storage_resolution,
                "Timestamp": datetime.now().replace(microsecond=0),
            }
        ]
        put_metric_data(namespace, metric_data, configuration, secrets)
        metric_value = metric_value + increment
        sleep(1)


###############################################################################
# Private functions
###############################################################################
def _remove_rule_targets(
    rule_name: str, target_ids: Union[str, List[str]], client: boto3.client
):
    """
    Removes provided CloudWatch rule targets.
    """
    logger.debug(
        "Removing {} targets from rule {}: {}".format(
            len(target_ids), rule_name, target_ids
        )
    )
    return client.remove_targets(Rule=rule_name, Ids=target_ids)


def _get_rule_target_ids(rule_name: str, client: boto3.client, limit: int = None):
    """
    Return all targets for a provided CloudWatch rule name.
    """
    request_kwargs = {
        "Rule": rule_name,
        **({"Limit": limit} if limit else {}),
    }

    targets = []
    while True:
        response = client.list_targets_by_rule(**request_kwargs)
        targets += response["Targets"]
        next_token = response.get("NextToken")
        if next_token is None:
            break
        request_kwargs["NextToken"] = next_token
    return [t["Id"] for t in targets]
