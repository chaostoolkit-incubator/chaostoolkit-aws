from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.cloudwatch.actions import (
    delete_rule,
    disable_rule,
    enable_rule,
    put_metric_data,
    put_rule,
    put_rule_targets,
    remove_rule_targets,
)


def mock_client_error(*args, **kwargs):
    return ClientError(
        operation_name=kwargs["op"],
        error_response={
            "Error": {"Code": kwargs["Code"], "Message": kwargs["Message"]}
        },
    )


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_put_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    schedule_expression = "rate(5 minutes)"
    state = "ENABLED"
    description = "My 5 minute rule"
    role_arn = "iam:role:for:my:rule"
    put_rule(
        rule_name,
        schedule_expression=schedule_expression,
        state=state,
        description=description,
        role_arn=role_arn,
    )
    client.put_rule.assert_called_with(
        Name=rule_name,
        ScheduleExpression=schedule_expression,
        State=state,
        Description=description,
        RoleArn=role_arn,
    )


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_put_rule_targets(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    targets = [
        {
            "Id": "1234",
            "Arn": "arn:aws:lambda:eu-central-1:"
            "101010101010:function:MyFunction",
        }
    ]
    put_rule_targets(rule_name, targets)
    client.put_targets.assert_called_with(Rule=rule_name, Targets=targets)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_disable_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    disable_rule(rule_name)
    client.disable_rule.assert_called_with(Name=rule_name)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_enable_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    enable_rule(rule_name)
    client.enable_rule.assert_called_with(Name=rule_name)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_delete_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    delete_rule(rule_name)
    client.delete_rule.assert_called_with(Name=rule_name)
    client.remove_targets.assert_not_called()


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_delete_rule_force(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    target_ids = ["1", "2", "3"]
    client.list_targets_by_rule.return_value = {
        "Targets": [{"Id": t} for t in target_ids]
    }
    rule_name = "my-rule"
    delete_rule(rule_name, force=True)
    client.delete_rule.assert_called_with(Name=rule_name)
    client.list_targets_by_rule.assert_called_with(Rule=rule_name)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_remove_rule_targets(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    target_ids = ["1", "2", "3"]
    remove_rule_targets(rule_name, target_ids)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_cloudwatch_remove_rule_targets_all(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = "my-rule"
    target_ids = ["1", "2", "3"]
    client.list_targets_by_rule.return_value = {
        "Targets": [{"Id": t} for t in target_ids]
    }
    remove_rule_targets(rule_name, target_ids=None)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)
    client.list_targets_by_rule.assert_called_with(Rule=rule_name)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_put_metric_data_valid_single_datapoint(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.put_metric_data.return_value = None
    time_stamp_1 = datetime.today() - timedelta(minutes=2)
    time_stamp_2 = datetime.today()

    put_metric_data(
        namespace="TestMetricNamespace",
        metric_data=[
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp_1,
                "Value": 85.568945236,
                "Unit": "Percent",
                "StorageResolution": 60,
            },
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp_2,
                "Value": 89.6854,
                "Unit": "Percent",
                "StorageResolution": 60,
            },
        ],
    )

    client.put_metric_data.assert_called_with(
        Namespace="TestMetricNamespace",
        MetricData=[
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp_1,
                "Value": 85.568945236,
                "Unit": "Percent",
                "StorageResolution": 60,
            },
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp_2,
                "Value": 89.6854,
                "Unit": "Percent",
                "StorageResolution": 60,
            },
        ],
    )


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_put_metric_data_valid_multi_datapoints(aws_client):
    time_stamp = datetime.today()
    client = MagicMock()
    aws_client.return_value = client
    client.put_metric_data.return_value = None

    put_metric_data(
        namespace="TestMetricNamespace",
        metric_data=[
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp,
                "Values": [5.5, 10.2, 6.5],
                "Counts": [1, 3, 2.6],
                "Unit": "Percent",
                "StorageResolution": 60,
            }
        ],
    )

    client.put_metric_data.assert_called_with(
        Namespace="TestMetricNamespace",
        MetricData=[
            {
                "MetricName": "MemoryUtilization",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": "i-000000000000"}
                ],
                "Timestamp": time_stamp,
                "Values": [5.5, 10.2, 6.5],
                "Counts": [1, 3, 2.6],
                "Unit": "Percent",
                "StorageResolution": 60,
            }
        ],
    )


@patch("chaosaws.cloudwatch.actions.aws_client", autospec=True)
def test_put_metric_data_invalid_parameter(aws_client):
    time_stamp = datetime.today()
    client = MagicMock()
    aws_client.return_value = client
    client.put_metric_data.side_effect = mock_client_error(
        op="PutMetricData",
        Code="InvalidParameterValueException",
        Message="An error occurred when calling PutMetricData",
    )

    with pytest.raises(FailedActivity) as x:
        put_metric_data(
            namespace="TestMetricNamespace",
            metric_data=[
                {
                    "MetricName": "MemoryUtilization",
                    "Dimensions": [
                        {"Name": "InstanceId", "Value": "i-000000000000"}
                    ],
                    "Timestamp": time_stamp,
                    "Value": 85.568945236,
                    "Unit": "InvalidUnit",
                    "StorageResolution": 60,
                }
            ],
        )
    assert "An error occurred when calling PutMetricData" in str(x)
