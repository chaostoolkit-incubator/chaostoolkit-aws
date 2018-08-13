# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaosaws.elbv2.probes import targets_health_count


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
    desired_response = {
        "TestTargetGroup1": {
            "healthy": 1
        },
        "TestTargetGroup2": {
            "unhealthy": 1
        }
    }
    response = targets_health_count(tg_names=tg_names)
    assert response == desired_response
