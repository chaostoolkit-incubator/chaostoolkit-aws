# -*- coding: utf-8 -*-
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from chaosaws.ec2.actions import (
    stop_instance, stop_instances, terminate_instance, terminate_instances)
from chaoslib.exceptions import FailedActivity


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {'Reservations':
                                              [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}
    stop_instance(inst_id)
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
    stop_instance(inst_id)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_id])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {'Reservations':
                                              [{'Instances': [{'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}
    stop_instance(inst_id, force=True)
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
    stop_instance(inst_id, force=True)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_id])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_ids = ["i-1234567890abcdef0", "i-987654321fedcba"]
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {'Reservations':
                                              [{'Instances': [
                                                  {'InstanceId': inst_ids[0], 'InstanceLifecycle': 'normal'}, {'InstanceId': inst_ids[1], 'InstanceLifecycle': 'spot', 'SpotInstanceRequestId': spot_request_id}]}]}
    stop_instances(inst_ids)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_ids[0]], Force=False)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_ids[1]])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_random_instance_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': inst_id,
                'InstanceLifecycle': 'normal'}]
        }]}

    stop_instance(az="us-west-1")
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
    client.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [
                {
                    'InstanceId': inst_1_id,
                    'InstanceLifecycle': 'normal'
                },
                {
                    'InstanceId': inst_2_id,
                    'InstanceLifecycle': 'spot',
                    'SpotInstanceRequestId': spot_request_id
                }
            ]}]}

    stop_instances(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(
        InstanceIds=[inst_2_id])


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
    client.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': inst_1_id,
                'InstanceLifecycle': 'normal'}]
        }]}

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

    stop_instances(filters=filters, az='us-west-2')

    called_filters = deepcopy(filters)
    called_filters.append(
        {'Name': 'availability-zone', 'Values': ['us-west-2']})
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_instance_with_no_lifecycle(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        'Reservations':
        [{'Instances': [{'InstanceId': inst_id}]}]
    }
    stop_instance(inst_id)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_stop_normal_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        'Reservations':
        [{'Instances': [{
            'InstanceId': inst_id,
            'InstanceLifecycle': 'normal'
        }]}]
    }
    stop_instance(inst_id)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_id], Force=False)


###
# Terminate Instance
###
def test_terminate_instance_no_values():
    with pytest.raises(FailedActivity) as x:
        terminate_instance()
    assert 'To terminate an EC2, you must specify the instance-id, ' \
           'an Availability Zone, or provide a set of filters' in str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_instance_az_no_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    az = 'us-west-2'
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': []}]}

    with pytest.raises(FailedActivity) as x:
        terminate_instance(az=az)
    assert 'No instances found matching filters: %s' % az


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_normal_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [{
            'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}
    terminate_instance(inst_id)
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_spot_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = 'sir-abcdef01'
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [{
            'InstanceId': inst_id, 'InstanceLifecycle': 'spot',
            'SpotInstanceRequestId': spot_request_id}]}]}
    terminate_instance(inst_id)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id])
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_random_az_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [{
            'InstanceId': inst_id, 'InstanceLifecycle': 'normal'}]}]}

    terminate_instance(az="us-west-1")
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_instance_by_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [{
            'InstanceId': inst_1_id, 'InstanceLifecycle': 'normal'}]}]}

    filters = [
        {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name': 'tag-value', 'Values': ['chaos-cluster']},
        {'Name': 'tag-key', 'Values': ['kubernetes.io/cluster/chaos-cluster']},
        {'Name': 'tag-value', 'Values': ['owned']},
        {'Name': 'tag-key',
         'Values': ['eksctl.cluster.k8s.io/v1alpha1/cluster-name']},
    ]
    terminate_instance(filters=filters, az='us-west-2')

    called_filters = deepcopy(filters)
    called_filters.append(
        {'Name': 'availability-zone', 'Values': ['us-west-2']})
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.terminate_instances.assert_called_with(InstanceIds=[inst_1_id])


###
# Terminate Instances
###
def test_terminate_instances_no_values():
    with pytest.raises(FailedActivity) as x:
        terminate_instances()
    assert 'To terminate instances, you must specify the instance-id, an ' \
           'Availability Zone, or provide a set of filters' in str(x)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_instances_az_no_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    az = 'us-west-2'
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': []}]}

    with pytest.raises(FailedActivity) as x:
        terminate_instances(az=az)
    assert 'No instances found matching filters: %s' % az


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_normal_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': instance_ids[0], 'InstanceLifecycle': 'normal'},
            {'InstanceId': instance_ids[1], 'InstanceLifecycle': 'normal'},
        ]}]}
    terminate_instances(instance_ids)
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_spot_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    spot_ids = ['sir-abcdef01', 'sir-fedcba10']
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': instance_ids[0],
             'InstanceLifecycle': 'spot',
             'SpotInstanceRequestId': spot_ids[0]},
            {'InstanceId': instance_ids[1],
             'InstanceLifecycle': 'spot',
             'SpotInstanceRequestId': spot_ids[1]},
        ]}]}
    terminate_instances(instance_ids)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=spot_ids)
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_random_az_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': instance_ids[0], 'InstanceLifecycle': 'normal'},
            {'InstanceId': instance_ids[1], 'InstanceLifecycle': 'normal'},
        ]}]}

    terminate_instances(az="us-west-1")
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_terminate_instances_by_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': instance_ids[0], 'InstanceLifecycle': 'normal'},
            {'InstanceId': instance_ids[1], 'InstanceLifecycle': 'normal'},
        ]}]}

    filters = [
        {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name': 'tag-value', 'Values': ['chaos-cluster']},
        {'Name': 'tag-key', 'Values': ['kubernetes.io/cluster/chaos-cluster']},
        {'Name': 'tag-value', 'Values': ['owned']},
        {'Name': 'tag-key',
         'Values': ['eksctl.cluster.k8s.io/v1alpha1/cluster-name']},
    ]
    terminate_instances(filters=filters, az='us-west-2')

    called_filters = deepcopy(filters)
    called_filters.append(
        {'Name': 'availability-zone', 'Values': ['us-west-2']})
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)
