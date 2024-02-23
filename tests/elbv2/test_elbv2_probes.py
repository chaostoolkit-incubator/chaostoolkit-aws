from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.elbv2.probes import (
    all_targets_healthy,
    is_access_log_enabled,
    targets_health_count,
)


@patch("chaosaws.elbv2.probes.aws_client", autospec=True)
def test_targets_health_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ["TestTargetGroup1", "TestTargetGroup2"]
    client.describe_target_groups.return_value = {
        "TargetGroups": [
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
                "TargetGroupName": "TestTargetGroup1",
            },
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
                "TargetGroupName": "TestTargetGroup2",
            },
        ]
    }
    client.describe_target_health.side_effect = [
        {"TargetHealthDescriptions": [{"TargetHealth": {"State": "healthy"}}]},
        {
            "TargetHealthDescriptions": [
                {"TargetHealth": {"State": "unhealthy"}}
            ]
        },
    ]
    response = targets_health_count(tg_names=tg_names)
    assert {"healthy": 1} in response.values()
    assert {"unhealthy": 1} in response.values()


@patch("chaosaws.elbv2.probes.aws_client", autospec=True)
def test_all_targets_healthy_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ["TestTargetGroup1", "TestTargetGroup2"]
    client.describe_target_groups.return_value = {
        "TargetGroups": [
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
                "TargetGroupName": "TestTargetGroup1",
            },
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
                "TargetGroupName": "TestTargetGroup2",
            },
        ]
    }
    client.describe_target_health.side_effect = [
        {"TargetHealthDescriptions": [{"TargetHealth": {"State": "healthy"}}]},
        {"TargetHealthDescriptions": [{"TargetHealth": {"State": "healthy"}}]},
    ]
    response = all_targets_healthy(tg_names=tg_names)
    assert response is True


@patch("chaosaws.elbv2.probes.aws_client", autospec=True)
def test_all_targets_healthy_false(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_names = ["TestTargetGroup1", "TestTargetGroup2"]
    client.describe_target_groups.return_value = {
        "TargetGroups": [
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
            """,
                "TargetGroupName": "TestTargetGroup1",
            },
            {
                "TargetGroupArn": """
            arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup2/234567890abcdef0
            """,
                "TargetGroupName": "TestTargetGroup2",
            },
        ]
    }
    client.describe_target_health.side_effect = [
        {"TargetHealthDescriptions": [{"TargetHealth": {"State": "healthy"}}]},
        {
            "TargetHealthDescriptions": [
                {"TargetHealth": {"State": "unhealthy"}}
            ]
        },
    ]
    response = all_targets_healthy(tg_names=tg_names)
    assert response is False


@patch("chaosaws.elbv2.probes.aws_client", autospec=True)
def test_is_access_log_enabled_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_load_balancer_attributes.return_value = {
        "Attributes": [
            {"Key": "access_logs.s3.enabled", "Value": "true"},
            {"Key": "access_logs.s3.bucket", "Value": ""},
        ]
    }
    lb_arn = (
        "arn:aws:elasticloadbalancing:eu-west-1:111111111111:"
        "loadbalancer/app/test-lb/1234567890abcdef"
    )

    response = is_access_log_enabled(load_balancer_arn=lb_arn)
    assert response is True


@patch("chaosaws.elbv2.probes.aws_client", autospec=True)
def test_is_access_log_enabled_false(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_load_balancer_attributes.return_value = {
        "Attributes": [
            {"Key": "access_logs.s3.enabled", "Value": "false"},
            {"Key": "access_logs.s3.bucket", "Value": ""},
        ]
    }
    lb_arn = (
        "arn:aws:elasticloadbalancing:eu-west-1:111111111111:loadbalancer"
        "/app/test-lb/1234567890abcdef"
    )
    response = is_access_log_enabled(load_balancer_arn=lb_arn)
    assert response is False


def test_targets_health_count_needs_tg_names():
    with pytest.raises(FailedActivity) as x:
        targets_health_count([])
    assert "Non-empty list of target groups is required" in str(x.value)


def test_all_targets_healthy_needs_tg_names():
    with pytest.raises(FailedActivity) as x:
        all_targets_healthy([])
    assert "Non-empty list of target groups is required" in str(x.value)
