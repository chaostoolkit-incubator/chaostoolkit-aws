# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaosaws.elbv2.actions import deregister_target


@patch('chaosaws.elbv2.actions.aws_client', autospec=True)
def test_deregister_target(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_name = 'TestTargetGroup1'
    tg_arn = """
    arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/TestTargetGroup1/1234567890abcdef
    """
    target_id = 'i-0123456789abcdef0'
    client.describe_target_groups.return_value = {"TargetGroups": [
        {
            'TargetGroupArn': tg_arn,
            'TargetGroupName': tg_name
        }
    ]}
    client.describe_target_health.return_value = {
        'TargetHealthDescriptions': [{
            'Target': {'Id': target_id}
        }]
    }
    response = deregister_target(tg_name=tg_name)
    client.deregister_targets.assert_called_with(
        TargetGroupArn=tg_arn, Targets=[{'Id': target_id}])
