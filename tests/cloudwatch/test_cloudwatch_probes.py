import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.cloudwatch.probes import (
    get_alarm_state_value,
    get_metric_data,
    get_metric_statistics,
)

module_path = os.path.dirname(os.path.abspath(__file__))
date_format = "%a, %d %b %Y %H:%M"


def datetime_parser(json_data: dict):
    for k, v in json_data.items():
        try:
            json_data[k] = datetime.strptime(v, datetime)
        except Exception:
            pass
    return json_data


@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_alarm_state_value_ok(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alarm_name = "my-alarm"
    client.describe_alarms.return_value = {
        "MetricAlarms": [{"AlarmName": alarm_name, "StateValue": "OK"}]
    }
    result = get_alarm_state_value(alarm_name)
    assert result == "OK"
    client.describe_alarms.assert_called_with(AlarmNames=[alarm_name])


@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_alarm_state_value_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alarm_name = "my-alarm"
    client.describe_alarms.return_value = {"MetricAlarms": []}
    with pytest.raises(FailedActivity):
        get_alarm_state_value(alarm_name)
    client.describe_alarms.assert_called_with(AlarmNames=[alarm_name])


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_metric_statistics_dimensions_ok(
    aws_client, mock_datetime
):
    client = MagicMock()
    aws_client.return_value = client
    mock_datetime.utcnow.return_value = datetime(
        2015, 1, 1, 15, 15, tzinfo=timezone.utc
    )

    namespace = "AWS/Lambda"
    metric_name = "Invocations"
    dimension_name = None
    dimension_value = None
    dimensions = [{"Name": "FunctionName", "Value": "MyFunction"}]
    duration = 120
    offset = 60
    statistic = "Sum"
    extended_statistic = None
    unit = "Count"
    client.get_metric_statistics.return_value = {
        "Datapoints": [{statistic: 4753.0}]
    }

    result = get_metric_statistics(
        namespace=namespace,
        metric_name=metric_name,
        dimension_name=dimension_name,
        dimension_value=dimension_value,
        dimensions=dimensions,
        duration=duration,
        offset=offset,
        statistic=statistic,
        extended_statistic=extended_statistic,
        unit=unit,
    )

    assert result == 4753.0
    client.get_metric_statistics.assert_called_with(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        Period=duration,
        StartTime=datetime(2015, 1, 1, 15, 12, tzinfo=timezone.utc),
        EndTime=datetime(2015, 1, 1, 15, 14, tzinfo=timezone.utc),
        Statistics=[statistic],
        Unit=unit,
    )


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_metric_statistics_ok(aws_client, mock_datetime):
    client = MagicMock()
    aws_client.return_value = client
    mock_datetime.utcnow.return_value = datetime(
        2015, 1, 1, 15, 15, tzinfo=timezone.utc
    )

    namespace = "AWS/Lambda"
    metric_name = "Invocations"
    dimension_name = "FunctionName"
    dimension_value = "MyFunction"
    duration = 120
    offset = 60
    statistic = "Sum"
    extended_statistic = None
    unit = "Count"
    client.get_metric_statistics.return_value = {
        "Datapoints": [{statistic: 4753.0}]
    }

    result = get_metric_statistics(
        namespace=namespace,
        metric_name=metric_name,
        dimension_name=dimension_name,
        dimension_value=dimension_value,
        duration=duration,
        offset=offset,
        statistic=statistic,
        extended_statistic=extended_statistic,
        unit=unit,
    )

    assert result == 4753.0
    client.get_metric_statistics.assert_called_with(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
        Period=duration,
        StartTime=datetime(2015, 1, 1, 15, 12, tzinfo=timezone.utc),
        EndTime=datetime(2015, 1, 1, 15, 14, tzinfo=timezone.utc),
        Statistics=[statistic],
        Unit=unit,
    )


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_metric_statistics_extended_ok(
    aws_client, mock_datetime
):
    client = MagicMock()
    aws_client.return_value = client
    mock_datetime.utcnow.return_value = datetime(
        2015, 1, 1, 15, 15, tzinfo=timezone.utc
    )

    namespace = "AWS/Lambda"
    metric_name = "Invocations"
    dimension_name = "FunctionName"
    dimension_value = "MyFunction"
    duration = 120
    offset = 60
    statistic = None
    extended_statistic = "p99"
    client.get_metric_statistics.return_value = {
        "Datapoints": [{"ExtendedStatistics": {extended_statistic: 4753.0}}]
    }
    unit = None

    result = get_metric_statistics(
        namespace=namespace,
        metric_name=metric_name,
        dimension_name=dimension_name,
        dimension_value=dimension_value,
        duration=duration,
        offset=offset,
        statistic=statistic,
        extended_statistic=extended_statistic,
        unit=unit,
    )

    assert result == 4753.0
    client.get_metric_statistics.assert_called_with(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
        Period=duration,
        StartTime=datetime(2015, 1, 1, 15, 12, tzinfo=timezone.utc),
        EndTime=datetime(2015, 1, 1, 15, 14, tzinfo=timezone.utc),
        ExtendedStatistics=[extended_statistic],
    )


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_metric_statistics_no_datapoints(
    aws_client, mock_datetime
):
    client = MagicMock()
    aws_client.return_value = client
    mock_datetime.utcnow.return_value = datetime(
        2015, 1, 1, 15, 15, tzinfo=timezone.utc
    )

    namespace = "AWS/Lambda"
    metric_name = "Invocations"
    dimension_name = "FunctionName"
    dimension_value = "MyFunction"
    duration = 120
    offset = 60
    statistic = "Sum"
    extended_statistic = None
    unit = "Count"
    client.get_metric_statistics.return_value = {"Datapoints": []}

    response = get_metric_statistics(
        namespace=namespace,
        metric_name=metric_name,
        dimension_name=dimension_name,
        dimension_value=dimension_value,
        duration=duration,
        offset=offset,
        statistic=statistic,
        extended_statistic=extended_statistic,
        unit=unit,
    )

    assert response == 0

    client.get_metric_statistics.assert_called_with(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
        Period=duration,
        StartTime=datetime(2015, 1, 1, 15, 12, tzinfo=timezone.utc),
        EndTime=datetime(2015, 1, 1, 15, 14, tzinfo=timezone.utc),
        Statistics=[statistic],
        Unit=unit,
    )


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_cloudwatch_get_metric_statistics_bad_response(
    aws_client, mock_datetime
):
    client = MagicMock()
    aws_client.return_value = client
    mock_datetime.utcnow.return_value = datetime(
        2015, 1, 1, 15, 15, tzinfo=timezone.utc
    )

    namespace = "AWS/Lambda"
    metric_name = "Invocations"
    dimension_name = "FunctionName"
    dimension_value = "MyFunction"
    duration = 120
    offset = 60
    statistic = "Sum"
    extended_statistic = None
    unit = "Count"
    client.get_metric_statistics.return_value = {
        "Datapoints": [{"some": "value"}]
    }

    with pytest.raises(FailedActivity):
        get_metric_statistics(
            namespace=namespace,
            metric_name=metric_name,
            dimension_name=dimension_name,
            dimension_value=dimension_value,
            duration=duration,
            offset=offset,
            statistic=statistic,
            extended_statistic=extended_statistic,
            unit=unit,
        )

    client.get_metric_statistics.assert_called_with(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
        Period=duration,
        StartTime=datetime(2015, 1, 1, 15, 12, tzinfo=timezone.utc),
        EndTime=datetime(2015, 1, 1, 15, 14, tzinfo=timezone.utc),
        Statistics=[statistic],
        Unit=unit,
    )


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_average_dimensions(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_full.json"), "r"
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "ActiveConnectionCount",
        "dimensions": [
            {
                "Name": "LoadBalancer",
                "Value": "app/my_test_alb/0000000000000000",
            }
        ],
        "period": 60,
        "duration": 300,
        "statistic": "Average",
        "unit": "Count",
    }
    response = get_metric_data(**args)
    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "ActiveConnectionCount",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Average",
                    "Unit": "Count",
                },
                "Label": "ActiveConnectionCount",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    assert response == 7.53


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_average(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_full.json")
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "ActiveConnectionCount",
        "dimension_name": "LoadBalancer",
        "dimension_value": "app/my_test_alb/0000000000000000",
        "period": 60,
        "duration": 300,
        "statistic": "Average",
        "unit": "Count",
    }
    response = get_metric_data(**args)
    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "ActiveConnectionCount",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Average",
                    "Unit": "Count",
                },
                "Label": "ActiveConnectionCount",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    assert response == 7.53


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_minimum(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_full.json")
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "ActiveConnectionCount",
        "dimension_name": "LoadBalancer",
        "dimension_value": "app/my_test_alb/0000000000000000",
        "period": 60,
        "duration": 300,
        "statistic": "Minimum",
        "unit": "Count",
    }
    response = get_metric_data(**args)
    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "ActiveConnectionCount",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Minimum",
                    "Unit": "Count",
                },
                "Label": "ActiveConnectionCount",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    assert response == 5.0


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_maximum(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_full.json")
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "ActiveConnectionCount",
        "dimension_name": "LoadBalancer",
        "dimension_value": "app/my_test_alb/0000000000000000",
        "period": 60,
        "duration": 300,
        "statistic": "Maximum",
        "unit": "Count",
    }
    response = get_metric_data(**args)
    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "ActiveConnectionCount",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Maximum",
                    "Unit": "Count",
                },
                "Label": "ActiveConnectionCount",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    assert response == 10.33


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_sum(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_full.json")
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "ActiveConnectionCount",
        "dimension_name": "LoadBalancer",
        "dimension_value": "app/my_test_alb/0000000000000000",
        "period": 60,
        "duration": 300,
        "statistic": "Sum",
        "unit": "Count",
    }
    response = get_metric_data(**args)
    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "ActiveConnectionCount",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Sum",
                    "Unit": "Count",
                },
                "Label": "ActiveConnectionCount",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    assert response == 37.67


@patch("chaosaws.cloudwatch.probes.datetime", autospec=True)
@patch("chaosaws.cloudwatch.probes.aws_client", autospec=True)
def test_get_cloudwatch_data_no_results(m_client, m_datetime):
    with open(
        os.path.join(module_path, "data", "cloudwatch_data_none.json")
    ) as fh:
        response_data = json.loads(fh.read(), object_hook=datetime_parser)
    client = MagicMock()
    m_client.return_value = client
    client.get_metric_data.return_value = response_data
    m_datetime.utcnow.return_value = datetime(
        2020, 1, 1, 17, 00, tzinfo=timezone.utc
    )

    args = {
        "namespace": "AWS/ApplicationELB",
        "metric_name": "HTTPCode_ELB_504_Count",
        "dimension_name": "LoadBalancer",
        "dimension_value": "app/my_test_alb/0000000000000000",
        "period": 60,
        "duration": 300,
        "statistic": "Average",
        "unit": "Count",
    }

    response = get_metric_data(**args)
    assert response == 0

    client.get_metric_data.assert_called_with(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApplicationELB",
                        "MetricName": "HTTPCode_ELB_504_Count",
                        "Dimensions": [
                            {
                                "Name": "LoadBalancer",
                                "Value": "app/my_test_alb/0000000000000000",
                            }
                        ],
                    },
                    "Period": 60,
                    "Stat": "Average",
                    "Unit": "Count",
                },
                "Label": "HTTPCode_ELB_504_Count",
            },
        ],
        StartTime=datetime(2020, 1, 1, 16, 55, tzinfo=timezone.utc),
        EndTime=datetime(2020, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
