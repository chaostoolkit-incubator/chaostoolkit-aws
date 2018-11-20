# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client

__all__ = ["get_alarm_state_value", "get_metric_statistics"]


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


def get_metric_statistics(namespace: str, metric_name: str,
                          dimension_name: str, dimension_value: str,
                          duration: int = 60, offset: int = 0,
                          statistic: str = None,
                          extended_statistic: str = None,
                          unit: str = None,
                          configuration: Configuration = None,
                          secrets: Secrets = None):
    """
    Get the value of a statistical calculation for a given metric.

    The period for which the calculation will be performed is specified by a duration and
    an offset from the current time. Both are specified in seconds.

    Example: A duration of 60 seconds and an offset of 30 seconds will yield a
    statistical value based on the time interval between 30 and 90 seconds in the past.

    More information about input parameters are available in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.get_metric_statistics
    """  # noqa: E501
    client = aws_client("cloudwatch", configuration, secrets)

    if statistic is None and extended_statistic is None:
        raise FailedActivity(
            'You must supply argument for statistic or extended_statistic'
        )

    end_time = datetime.utcnow() - timedelta(seconds=offset)
    start_time = end_time - timedelta(seconds=duration)
    request_kwargs = {
        'Namespace': namespace,
        'MetricName': metric_name,
        'Dimensions': [{
            'Name': dimension_name,
            'Value': dimension_value
        }],
        'StartTime': start_time,
        'EndTime': end_time,
        'Period': duration
    }

    if statistic is not None:
        request_kwargs['Statistics'] = [statistic]
    if extended_statistic is not None:
        request_kwargs['ExtendedStatistics'] = [extended_statistic]
    if unit is not None:
        request_kwargs['Unit'] = unit

    logger.debug('Request arguments: {}'.format(request_kwargs))
    response = client.get_metric_statistics(**request_kwargs)

    datapoints = response['Datapoints']
    if len(datapoints) == 0:
        raise FailedActivity(
            "No datapoints found for metric {}.{}.{}.{}".format(
                namespace, metric_name, dimension_name, dimension_value
            )
        )

    datapoint = datapoints[0]
    logger.debug('Response: {}'.format(response))
    try:
        if statistic is not None:
            return datapoint[statistic]
        elif extended_statistic is not None:
            return datapoint['ExtendedStatistics'][extended_statistic]
    except Exception as x:
        raise FailedActivity(
            "Unable to parse response '{}': '{}'".format(response, str(x))
        )
