# -*- coding: utf-8 -*-
from copy import deepcopy
from unittest.mock import MagicMock, patch

from chaoslib.exceptions import FailedActivity
import pytest

from chaosaws.ec2.actions import stop_instance, stop_instances


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {'Reservations':
            [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}
    response = stop_instance(inst_id)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_spot_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {'Reservations':
            [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'spot', 'SpotInstanceRequestId': spot_request_id}]}]}
    response = stop_instance(inst_id)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {'Reservations':
            [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}
    response = stop_instance(inst_id, force=True)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=True)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_spot_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {'Reservations':
            [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'spot', 'SpotInstanceRequestId': spot_request_id}]}]}
    response = stop_instance(inst_id, force=True)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_id], Force=True)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_ids = ["i-1234567890abcdef0", "i-987654321fedcba"]
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {'Reservations':
        [{'Instances': [
            {'InstanceId': inst_ids[0], 'InstanceLifecycle': 'normal'}, {'InstanceId': inst_ids[1], 'InstanceLifecycle': 'spot', 'SpotInstanceRequestId': spot_request_id}]}]}
    response = stop_instances(inst_ids)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_ids[0]], Force=False)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_ids[1]], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_random_instance_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {'Reservations':
            [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}

    response = stop_instance(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


def test_stop_random_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instance()
    assert "stop an EC2 instance, you must specify either the instance id," \
           " an AZ to pick a random instance from, or a set of filters." in \
           str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_all_instances_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    inst_2_id = "i-123456789abcdef"
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {'Reservations':
        [{'Instances': [
            {'InstanceId': inst_1_id, 'InstanceLifecycle': 'normal'}, {'InstanceId': inst_2_id, 'InstanceLifecycle': 'spot', 'SpotInstanceRequestId': spot_request_id}]}]}

    response = stop_instances(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_2_id], Force=False)


def test_stop_all_instances_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instances()
    assert "To stop EC2 instances, you must specify either the instance ids," \
           " an AZ to pick random instances from, or a set of filters." in \
           str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_all_instances_may_not_have_any_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = {'Reservations':
        [{'Instances': []}]}

    with pytest.raises(FailedActivity) as x:
        stop_instances(az="us-west-1")
    assert "No instances in availability zone: us-west-1" in str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance_by_specific_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    client.describe_instances.return_value = {'Reservations':
        [{'Instances': [{'InstanceId': inst_1_id, 'InstanceLifecycle': 'normal'}]}]}

    filters = [
        {
            'Name': 'instance-state-name',
            'Values': ['running'],
        },
        {
            'Name': 'tag-key', 
            'Values': ['eksctl.cluster.k8s.io/v1alpha1/cluster-name']
        },
        {
            'Name': 'tag-value',
            'Values': ['chaos-cluster']
        },
        {
            'Name': 'tag-key', 
            'Values': ['kubernetes.io/cluster/chaos-cluster']
        },
        {
            'Name': 'tag-value',
            'Values': ['owned']
        }
    ]

    response = stop_instances(filters=filters, az='us-west-2')

    called_filters = deepcopy(filters)
    called_filters.append(
        {'Name': 'availability-zone', 'Values': ['us-west-2']})
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False)
