# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger
from chaosaws import aws_client

__all__ = ["get_alarm_state_value", "get_metric_statistics", "get_metric_data"]


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
                          dimension_name: str = None, dimension_value: str = None,
                          dimensions: List[Dict[str, Any]] = None,
                          duration: int = 60, offset: int = 0,
                          statistic: str = None,
                          extended_statistic: str = None,
                          unit: str = None,
                          configuration: Configuration = None,
                          secrets: Secrets = None):
    """
    Get the value of a statistical calculation for a given metric.

        :param namespace: The AWS metric namespace
        :param metric_name: The name of the metric to pull data for
        :One of:
            params: dimension_name, dimension_value: Required to search for ONE dimension
            param: dimensions: Required to search for dimensions combinations 
            Are expected as a list of dictionary objects: [ {‘Name’: ‘DimName1’, ‘Value’: ‘Value1’}, {‘Name’: ‘DimName2’, ‘Value’: ‘Value2’}, … ] 
        :param unit: The type of unit desired to be collected
        :param statistic: The type of data to return
            One of: Average, Sum, Minimum, Maximum, SampleCount
        :param period: The window in which to pull datapoints for
        :param offset: The time (seconds) to offset the endtime (from now)
        :param duration: The time (seconds) to set the start time (from now)

    More information about input parameters are available in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.get_metric_statistics
    """  # noqa: E501
    client = aws_client("cloudwatch", configuration, secrets)

    if statistic is None and extended_statistic is None:
        raise FailedActivity(
            'You must supply argument for statistic or extended_statistic'
        )
    if dimensions is None and dimension_name is None and dimension_value is None:
        raise FailedActivity(
            'You must supply argument for dimensions'
        )

    end_time = datetime.utcnow() - timedelta(seconds=offset)
    start_time = end_time - timedelta(seconds=duration)
    request_kwargs = {
        'Namespace': namespace,
        'MetricName': metric_name,
        'StartTime': start_time,
        'EndTime': end_time,
        'Period': duration
    }
    if dimensions is not None:
        request_kwargs['Dimensions'] = dimensions
    if dimension_name and dimension_value is not None:
        request_kwargs['Dimensions'] = [{'Name': dimension_name, 'Value': dimension_value}]

    if statistic is not None:
        request_kwargs['Statistics'] = [statistic]
    if extended_statistic is not None:
        request_kwargs['ExtendedStatistics'] = [extended_statistic]
    if unit is not None:
        request_kwargs['Unit'] = unit

    logger.debug('Request arguments: {}'.format(request_kwargs))
    response = client.get_metric_statistics(**request_kwargs)

    datapoints = response['Datapoints']
    if not datapoints:
        return 0

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


def get_metric_data(namespace: str, metric_name: str,
                    dimension_name: str = None, dimension_value: str = None,
                    dimensions: List[Dict[str, Any]] = None, statistic: str = None,
                    duration: int = 300, period: int = 60, offset: int = 0,
                    unit: str = None, configuration: Configuration = None,
                    secrets: Secrets = None) -> float:
    """
    Gets metric data for a given metric in a given time period. This method
    allows for more data to be retrieved than get_metric_statistics.

        :param namespace: The AWS metric namespace
        :param metric_name: The name of the metric to pull data for
        :One of:
            :params dimension_name, dimension_value: Required to search for ONE dimension
            :param dimensions: Required to search for dimensions combinations 
            Are expected as a list of dictionary objects: [ {‘Name’: ‘DimName1’, ‘Value’: ‘Value1’}, {‘Name’: ‘DimName2’, ‘Value’: ‘Value2’}, … ]
        :param unit: The type of unit desired to be collected
        :param statistic: The type of data to return
            One of: Average, Sum, Minimum, Maximum, SampleCount
        :param period: The window in which to pull datapoints for
        :param offset: The time (seconds) to offset the endtime (from now)
        :param duration: The time (seconds) to set the start time (from now)

    More information about input parameters are available in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.get_metric_data
    """
    start_time = datetime.utcnow() - timedelta(seconds=duration)
    end_time = datetime.utcnow() - timedelta(seconds=offset)
    
    if dimensions is None and dimension_name is None and dimension_value is None:
        raise FailedActivity(
            'You must supply argument for dimensions'
        )
        
    args = {
        'MetricDataQueries': [{
            'Id': 'm1',
            'MetricStat': {
                'Metric': {
                    'Namespace': namespace,
                    'MetricName': metric_name,
                },
                'Period': period,
                'Stat': statistic
            },
            'Label': metric_name,
        }],
        'StartTime': start_time,
        'EndTime': end_time
    }

    if unit:
        args['MetricDataQueries'][0]['MetricStat']['Unit'] = unit
    if dimensions:
        args['MetricDataQueries'][0]['MetricStat']['Metric']['Dimensions'] = dimensions
    if dimension_name and dimension_value:
        args['MetricDataQueries'][0]['MetricStat']['Metric']['Dimensions'] = [{'Name': dimension_name, 'Value': dimension_value}]

    client = aws_client('cloudwatch', configuration, secrets)
    response = client.get_metric_data(**args)['MetricDataResults']

    results = {}
    for r in response:
        results.setdefault(r['Label'], []).extend(r['Values'])

    result = 0
    for k, v in results.items():
        if not v:
            continue

        if statistic == 'Sum':
            result = sum(v)
        elif statistic == 'Minimum':
            result = min(v)
        elif statistic == 'Maximum':
            result = max(v)
        else:
            result = mean(v)

    return round(result, 2)
