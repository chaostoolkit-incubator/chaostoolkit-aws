# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest
from tests.zpharmacy import Pharmacy
from chaosaws.elbv2.probes import (
    monitor, all_targets_healthy, targets_health_count)
from chaosaws.ec2.actions import terminate_instance, stop_instance
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


class TestMonitorELB(Pharmacy):
    def test_monitor_targets_health_count(self):
        session = self.replay('test_monitor_elbv2_targets_health_count')
        tg_name = 'generic-tg'
        params = {
            'probe_name': 'targets_health_count',
            'probe_args': {'tg_names': [tg_name]},
            'json_path': '"%s".healthy' % tg_name,
            'disrupted': 2,
            'recovered': 3,
            'delay': 1,
            'configuration': {
                'aws_session': session,
                'aws_region': 'us-east-1'
            }
        }

        targs = {
            'instance_id': 'i-00000000000000000',
            'configuration': {
                'aws_session': session,
                'aws_region': 'us-east-1'
            }
        }
        terminate_instance(**targs)
        results = monitor(**params)
        self.assertEqual(results['ctk:monitor_results'], 'success')

    def test_monitor_all_targets_healthy(self):
        session = self.replay('test_monitor_elbv2_all_targets_healthy')
        tg_name = 'generic_target_group'
        params = {
            'probe_name': 'all_targets_healthy',
            'probe_args': {'tg_names': [tg_name]},
            'disrupted': False,
            'recovered': True,
            'delay': 1,
            'configuration': {
                'aws_session': session,
                'aws_region': 'us-east-1'
            }
        }

        targs = {
            'instance_id': 'i-00000000000000001',
            'configuration': {
                'aws_session': session,
                'aws_region': 'us-east-1'
            }
        }
        stop_instance(**targs)
        results = monitor(**params)
        self.assertEqual(results['ctk:monitor_results'], 'success')
