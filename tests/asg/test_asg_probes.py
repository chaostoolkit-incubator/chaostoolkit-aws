# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest

from chaosaws.asg.probes import (desired_equals_healthy,
                                 desired_equals_healthy_tags)
from chaoslib.exceptions import FailedActivity


@patch('chaosaws.asg.probes.aws_client', autospec=True)
def test_desired_equals_healthy_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup1', 'AutoScalingGroup2']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy"
            }]
        }]
    }
    assert desired_equals_healthy(asg_names=asg_names) is True


@patch('chaosaws.asg.probes.aws_client', autospec=True)
def test_desired_equals_healthy_false(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup1', 'AutoScalingGroup2']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Unhealthy"
            }]
        }]
    }
    assert desired_equals_healthy(asg_names=asg_names) is False


@patch('chaosaws.asg.probes.aws_client', autospec=True)
def test_desired_equals_healthy_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup1', 'AutoScalingGroup2']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
        ]
    }
    assert desired_equals_healthy(asg_names=asg_names) is False


def test_desired_equals_healthy_needs_asg_names():
    with pytest.raises(FailedActivity) as x:
        desired_equals_healthy([])
    assert "Non-empty list of auto scaling groups is required" in str(x)


def desired_equals_healthy_tags_true_sideeffect(*args, **kwargs):
    if 'AutoScalingGroupNames' not in kwargs:
        return {
            "AutoScalingGroups": [
                {
                    'AutoScalingGroupName': 'AutoScalingGroup1',
                    "DesiredCapacity": 1,
                    "Instances": [{
                        "HealthStatus": "Healthy"
                    }],
                    'Tags': [{
                        'ResourceId': 'AutoScalingGroup1',
                        'Key': 'Application',
                        'Value': 'mychaosapp'
                    }]
                },
                {
                    'AutoScalingGroupName': 'AutoScalingGroup2',
                    "DesiredCapacity": 1,
                    "Instances": [{
                        "HealthStatus": "Unhealthy"
                    }],
                    'Tags': [{
                        'ResourceId': 'AutoScalingGroup1',
                        'Key': 'Application',
                        'Value': 'NOTmychaosapp'
                    }]
                },
                {
                    'AutoScalingGroupName': 'AutoScalingGroup3',
                    "DesiredCapacity": 1,
                    "Instances": [{
                        "HealthStatus": "Unhealthy"
                    }],
                    'Tags': [{
                        'ResourceId': 'AutoScalingGroup1',
                        'Key': 'NOTApplication',
                        'Value': 'mychaosapp'
                    }]
                }
            ]
        }
    else:
        return {
            "AutoScalingGroups": [
                {
                    'AutoScalingGroupName': 'AutoScalingGroup1',
                    "DesiredCapacity": 1,
                    "Instances": [{
                        "HealthStatus": "Healthy"
                    }],
                    'Tags': [{
                        'ResourceId': 'AutoScalingGroup1',
                        'Key': 'Application',
                        'Value': 'mychaosapp'
                    }]
                }
            ]
        }


@patch('chaosaws.asg.probes.aws_client', autospec=True)
def test_desired_equals_healthy_tags_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{'Key': 'Application', 'Value': 'mychaosapp'}]
    client.describe_auto_scaling_groups.side_effect = \
        desired_equals_healthy_tags_true_sideeffect
    assert desired_equals_healthy_tags(tags=tags) is True


@patch('chaosaws.asg.probes.aws_client', autospec=True)
def test_desired_equals_healthy_tags_false(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{'Key': 'Application', 'Value': 'mychaosapp'}]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                'AutoScalingGroupName': 'AutoScalingGroup1',
                "DesiredCapacity": 1,
                "Instances": [{
                    "HealthStatus": "Unhealthy"
                }],
                'Tags': [{
                    'ResourceId': 'AutoScalingGroup1',
                    'Key': 'Application',
                    'Value': 'mychaosapp'
                }]
            },
            {
                'AutoScalingGroupName': 'AutoScalingGroup2',
                "DesiredCapacity": 1,
                "Instances": [{
                    "HealthStatus": "Unhealthy"
                }],
                'Tags': [{
                    'ResourceId': 'AutoScalingGroup1',
                    'Key': 'Application',
                    'Value': 'NOTmychaosapp'
                }]
            },
            {
                'AutoScalingGroupName': 'AutoScalingGroup3',
                "DesiredCapacity": 1,
                "Instances": [{
                    "HealthStatus": "Unhealthy"
                }],
                'Tags': [{
                    'ResourceId': 'AutoScalingGroup1',
                    'Key': 'NOTApplication',
                    'Value': 'mychaosapp'
                }]
            }
        ]
    }
    assert desired_equals_healthy_tags(tags=tags) is False
