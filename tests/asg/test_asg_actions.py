# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
from chaoslib.exceptions import FailedActivity
from chaosaws.asg.actions import (suspend_processes, resume_processes)

import pytest


def test_suspend_process_no_name_or_tag():
    with pytest.raises(FailedActivity) as x:
        suspend_processes()
    assert 'one of the following arguments are required: ' \
           'asg_names or tags' in str(x)


def test_suspend_process_both_name_and_tag_one():
    with pytest.raises(FailedActivity) as x:
        suspend_processes(
            asg_names=['AutoScalingGroup-A'],
            tags=[{"Key": "TagKey", "Values": ["TagValues"]}])
    assert 'only one of the following arguments are allowed: ' \
           'asg_names/tags' in str(x)


def test_suspend_process_invalid_process():
    with pytest.raises(FailedActivity) as x:
        suspend_processes(
            asg_names=['AutoScalingGroup-A'],
            process_names=['Lunch'])
    assert "invalid process(es): ['Lunch'] not in" in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_suspend_process_asg_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": []
        }]
    }
    suspend_processes(asg_names=asg_names)
    client.suspend_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0])


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_suspend_process_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    client.get_paginator.return_value.paginate.return_value = [{
        'Tags': [{
            'ResourceId': 'AutoScalingGroup-A',
            'ResourceType': 'auto-scaling-group',
            'Key': 'TargetKey',
            'Value': 'TargetValue',
            'PropagateAtLaunch': False}]
    }]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": []
        }]
    }
    suspend_processes(tags=[{'Key': 'TargetKey', 'Value': 'TargetValue'}])
    client.suspend_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0])


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_suspend_process_asg_invalid_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": []}
    with pytest.raises(FailedActivity) as x:
        suspend_processes(asg_names=asg_names, process_names=["Launch"])
    assert 'Unable to locate ASG(s): %s' % asg_names in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_suspend_process_asg_invalid_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A', 'AutoScalingGroup-B']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": []
        }]
    }
    with pytest.raises(FailedActivity) as x:
        suspend_processes(asg_names=asg_names, process_names=["Launch"])
    assert 'No ASG(s) found with name(s): %s' % ([asg_names[1]]) in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_suspend_process_asg_invalid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{'Key': 'TargetKey', 'Value': 'TargetValue'}]
    client.get_paginator.return_value.paginate.return_value = [{'Tags': []}]
    with pytest.raises(FailedActivity) as x:
        suspend_processes(tags=tags)
    assert 'No ASG(s) found with matching tag(s): %s.' % tags in str(x)


def test_resume_process_no_name_or_tag():
    with pytest.raises(FailedActivity) as x:
        resume_processes()
    assert 'one of the following arguments are required: ' \
           'asg_names or tags' in str(x)


def test_resume_process_both_name_and_tag():
    with pytest.raises(FailedActivity) as x:
        resume_processes(
            asg_names=['AutoScalingGroup-A'],
            tags=[{"Key": "TagKey", "Values": ["TagValues"]}])
    assert 'only one of the following arguments are allowed: ' \
           'asg_names/tags' in str(x)


def test_resume_process_invalid_process():
    with pytest.raises(FailedActivity) as x:
        resume_processes(
            asg_names=['AutoScalingGroup-A'],
            process_names=['Lunch'])
    assert "invalid process(es): ['Lunch'] not in" in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_resume_process_asg_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": [{"ProcessName": "Launch"}]
        }]
    }
    resume_processes(asg_names=asg_names, process_names=["Launch"])
    client.resume_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0], ScalingProcesses=["Launch"])


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_resume_process_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    tags = [{'Key': 'TargetKey', 'Value': 'TargetValue'}]
    client.get_paginator.return_value.paginate.return_value = [{
        'Tags': [{
            'ResourceId': 'AutoScalingGroup-A',
            'ResourceType': 'auto-scaling-group',
            'Key': 'TargetKey',
            'Value': 'TargetValue',
            'PropagateAtLaunch': False}]
    }]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": [{"ProcessName": "Launch"}]
        }]
    }
    resume_processes(tags=tags, process_names=["Launch"])
    client.resume_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0], ScalingProcesses=["Launch"])


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_resume_process_asg_invalid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{'Key': 'TargetKey', 'Value': 'TargetValue'}]
    client.get_paginator.return_value.paginate.return_value = [{'Tags': []}]
    with pytest.raises(FailedActivity) as x:
        resume_processes(tags=tags)
    assert 'No ASG(s) found with matching tag(s): %s.' % tags in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_resume_process_asg_invalid_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": []}
    with pytest.raises(FailedActivity) as x:
        resume_processes(asg_names=asg_names, process_names=["Launch"])
    assert 'Unable to locate ASG(s): ' in str(x)


@patch('chaosaws.asg.actions.aws_client', autospec=True)
def test_resume_process_asg_invalid_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ['AutoScalingGroup-A', 'AutoScalingGroup-B']
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [{
            "AutoScalingGroupName": "AutoScalingGroup-A",
            "DesiredCapacity": 1,
            "Instances": [{
                "HealthStatus": "Healthy",
                "LifecycleState": "InService"
            }],
            "SuspendedProcesses": [{"ProcessName": "Launch"}]
        }]
    }
    with pytest.raises(FailedActivity) as x:
        resume_processes(asg_names=asg_names, process_names=["Launch"])
    assert 'No ASG(s) found with name(s): %s' % ([asg_names[1]]) in str(x)
