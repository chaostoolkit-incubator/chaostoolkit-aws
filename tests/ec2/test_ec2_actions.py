# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaoslib.exceptions import FailedActivity
import pytest

from chaosaws.ec2.actions import stop_instance, stop_instances


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    response = stop_instance(inst_id)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    response = stop_instance(inst_id, force=True)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=True)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_ids = ["i-1234567890abcdef0", "i-987654321fedcba"]
    response = stop_instances(inst_ids)
    client.stop_instances.assert_called_with(
        InstanceIds=inst_ids, Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_random_instance_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {'Reservations': 
        [{'Instances': [{'InstanceId': inst_id}]}]}

    response = stop_instance(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


def test_stop_random_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instance()
    assert "To stop an EC2 instance, you must specify an AZ to pick a " \
           "random instance from or the instance id to stop" in str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_all_instances_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    inst_2_id = "i-123456789abcdef"
    client.describe_instances.return_value = {'Reservations': 
        [{'Instances': [
            {'InstanceId': inst_1_id}, {'InstanceId': inst_2_id}]}]}

    response = stop_instances(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id, inst_2_id], Force=False)


def test_stop_all_instances_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instances()
    assert "To stop EC2 instances, you must specify the AZ or the list of " \
           "instances to stop" in str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_all_instances_may_not_have_any_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = {'Reservations': 
        [{'Instances': []}]}

    with pytest.raises(FailedActivity) as x:
        stop_instances(az="us-west-1")
    assert "No instances in availability zone: us-west-1" in str(x)
