# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client

__all__ = ["get_alarm_state_value"]


def get_alarm_state_value(alarm_name: str,
                          configuration: Configuration = None,
                          secrets: Secrets = None) -> str:
    """
    Return the state value of an alarm.

    The possbile alarm state values are described in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms
    """  # noqa: E501
    client = aws_client("cloudwatch", configuration, secrets)
    response = client.describe_alarms(AlarmNames=[alarm_name])
    if len(response["MetricAlarms"]) == 0:
        raise FailedActivity(
            "CloudWatch alarm name {} not found".format(alarm_name)
        )
    return response["MetricAlarms"][0]["StateValue"]
