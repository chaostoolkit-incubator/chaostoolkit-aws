from unittest.mock import MagicMock, patch

import pytest

from chaosaws.elbv2.probes import all_targets_healthy, targets_health_count
from chaoslib.exceptions import FailedActivity


@patch('chaosaws.elbv2.probes.aws_client', autospec=True)
def test_targets_health_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ['TestTargetGroup1', 'TestTargetGroup2']
    client.describe_target_groups.return_value = {"TargetGroups": [
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
            'TargetGroupName': 'TestTargetGroup1'
        },
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
            'TargetGroupName': 'TestTargetGroup2'
        }
    ]}
    client.describe_target_health.side_effect = [
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'healthy'}
            }]
        },
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'unhealthy'}
            }]
        }
    ]
    response = targets_health_count(tg_names=tg_names)
    assert {'healthy': 1} in response.values()
    assert {'unhealthy': 1} in response.values()


@patch('chaosaws.elbv2.probes.aws_client', autospec=True)
def test_all_targets_healthy_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ['TestTargetGroup1', 'TestTargetGroup2']
    client.describe_target_groups.return_value = {"TargetGroups": [
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
            'TargetGroupName': 'TestTargetGroup1'
        },
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
            'TargetGroupName': 'TestTargetGroup2'
        }
    ]}
    client.describe_target_health.side_effect = [
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'healthy'}
            }]
        },
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'healthy'}
            }]
        }
    ]
    response = all_targets_healthy(tg_names=tg_names)
    assert response is True


@patch('chaosaws.elbv2.probes.aws_client', autospec=True)
def test_all_targets_healthy_false(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ['TestTargetGroup1', 'TestTargetGroup2']
    client.describe_target_groups.return_value = {"TargetGroups": [
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
            'TargetGroupName': 'TestTargetGroup1'
        },
        {
            'TargetGroupArn': """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
            'TargetGroupName': 'TestTargetGroup2'
        }
    ]}
    client.describe_target_health.side_effect = [
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'healthy'}
            }]
        },
        {
            'TargetHealthDescriptions': [{
                'TargetHealth': {'State': 'unhealthy'}
            }]
        }
    ]
    response = all_targets_healthy(tg_names=tg_names)
    assert response is False


def test_targets_health_count_needs_tg_names():
    with pytest.raises(FailedActivity) as x:
        targets_health_count([])
    assert "Non-empty list of target groups is required" in str(x.value)


def test_all_targets_healthy_needs_tg_names():
    with pytest.raises(FailedActivity) as x:
        all_targets_healthy([])
    assert "Non-empty list of target groups is required" in str(x.value)
