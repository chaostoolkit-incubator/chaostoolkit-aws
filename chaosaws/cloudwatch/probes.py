from datetime import datetime, timedelta
from statistics import mean

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client

__all__ = ["get_alarm_state_value", "get_metric_statistics", "get_metric_data"]


def get_alarm_state_value(
    alarm_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> str:
    """
    Return the state value of an alarm.

    The possbile alarm state values are described in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms
    """  # noqa: E501
    client = aws_client("cloudwatch", configuration, secrets)
    response = client.describe_alarms(AlarmNames=[alarm_name])
    if len(response["MetricAlarms"]) == 0:
        raise FailedActivity(f"CloudWatch alarm name {alarm_name} not found")
    return response["MetricAlarms"][0]["StateValue"]


def get_metric_statistics(
    namespace: str,
    metric_name: str,
    dimension_name: str,
    dimension_value: str,
    duration: int = 60,
    offset: int = 0,
    statistic: str = None,
    extended_statistic: str = None,
    unit: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
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
            "You must supply argument for statistic or extended_statistic"
        )

    end_time = datetime.utcnow() - timedelta(seconds=offset)
    start_time = end_time - timedelta(seconds=duration)
    request_kwargs = {
        "Namespace": namespace,
        "MetricName": metric_name,
        "Dimensions": [{"Name": dimension_name, "Value": dimension_value}],
        "StartTime": start_time,
        "EndTime": end_time,
        "Period": duration,
    }

    if statistic is not None:
        request_kwargs["Statistics"] = [statistic]
    if extended_statistic is not None:
        request_kwargs["ExtendedStatistics"] = [extended_statistic]
    if unit is not None:
        request_kwargs["Unit"] = unit

    logger.debug(f"Request arguments: {request_kwargs}")
    response = client.get_metric_statistics(**request_kwargs)

    datapoints = response["Datapoints"]
    if not datapoints:
        return 0

    datapoint = datapoints[0]
    logger.debug(f"Response: {response}")
    try:
        if statistic is not None:
            return datapoint[statistic]
        elif extended_statistic is not None:
            return datapoint["ExtendedStatistics"][extended_statistic]
    except Exception as x:
        raise FailedActivity(f"Unable to parse response '{response}': '{str(x)}'")


def get_metric_data(
    namespace: str,
    metric_name: str,
    dimension_name: str,
    dimension_value: str,
    statistic: str = None,
    duration: int = 300,
    period: int = 60,
    offset: int = 0,
    unit: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> float:
    """Gets metric data for a given metric in a given time period. This method
    allows for more data to be retrieved than get_metric_statistics

    :params
        namespace: The AWS metric namespace
        metric_name: The name of the metric to pull data for
        dimension_name: The name of the dimension to search for
        dimension_value: The value to be used for searching the dimension
        unit: The type of unit desired to be collected
        statistic: The type of data to return.
            One of: Average, Sum, Minimum, Maximum, SampleCount
        period: The window in which to pull datapoints for
        offset: The time (seconds) to offset the endtime (from now)
        duration: The time (seconds) to set the start time (from now)
    """
    start_time = datetime.utcnow() - timedelta(seconds=duration)
    end_time = datetime.utcnow() - timedelta(seconds=offset)
    args = {
        "MetricDataQueries": [
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric_name,
                        "Dimensions": [
                            {"Name": dimension_name, "Value": dimension_value}
                        ],
                    },
                    "Period": period,
                    "Stat": statistic,
                },
                "Label": metric_name,
            }
        ],
        "StartTime": start_time,
        "EndTime": end_time,
    }

    if unit:
        args["MetricDataQueries"][0]["MetricStat"]["Unit"] = unit

    client = aws_client("cloudwatch", configuration, secrets)
    response = client.get_metric_data(**args)["MetricDataResults"]

    results = {}
    for r in response:
        results.setdefault(r["Label"], []).extend(r["Values"])

    result = 0
    for k, v in results.items():
        if not v:
            continue

        if statistic == "Sum":
            result = sum(v)
        elif statistic == "Minimum":
            result = min(v)
        elif statistic == "Maximum":
            result = max(v)
        else:
            result = mean(v)

    return round(result, 2)
