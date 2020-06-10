# -*- coding: utf-8 -*-
import pytest

from unittest.mock import MagicMock, patch
from tests.zpharmacy import Pharmacy

from chaosaws.ec2.probes import (
    describe_instances, count_instances, instance_state, monitor)
from chaosaws.ec2.actions import terminate_instance
from chaoslib.exceptions import FailedActivity


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_describe_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{'Name': 'availability-zone', 'Values': ["us-west-1"]}]
    describe_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_count_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{'Name': 'availability-zone', 'Values': ["us-west-1"]}]
    count_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_instance_state_no_state(aws_client):
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    with pytest.raises(TypeError) as x:
        instance_state(instance_ids=instance_ids)
    assert "missing 1 required positional argument: 'state'" in str(x.value)


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_instance_state_no_query(aws_client):
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    with pytest.raises(FailedActivity) as x:
        instance_state(state='running')
    assert 'Probe "instance_state" missing required parameter ' \
           '"instance_ids" or "filters"' in str(x.value)


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_instance_state(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ['i-987654321fedcba', 'i-392024ac3252ecb']
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': instance_ids[0], 'State': {'Name': 'running'}},
            {'InstanceId': instance_ids[1], 'State': {'Name': 'running'}},
        ]}]}
    results = instance_state(
        state='running',
        instance_ids=instance_ids)
    client.describe_instances.assert_called_with(InstanceIds=instance_ids)
    assert results


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_instance_state_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{'Name': 'instance-type', 'Values': ['t2.large']}]
    client.describe_instances.return_value = {
        'Reservations': [{'Instances': [
            {'InstanceId': 'i-987654321fedcba',
             'State': {'Name': 'running'},
             'InstanceType': 't2.large'}]}]}
    results = instance_state(
        state='running',
        filters=filters)
    client.describe_instances.assert_called_with(Filters=filters)
    assert results


class TestProbesEC2(Pharmacy):
    def test_monitor_ec2_describe(self):
        session = self.replay('test_monitor_ec2_describe')

        configuration = {'aws_session': session, 'aws_region': 'us-east-1'}

        params = {
            'probe_name': 'describe_instances',
            'probe_args': {
                'filters': [
                    {
                        'Name': 'instance-id',
                        'Values': ['i-00000000000000000']
                    }
                ]
            },
            'timeout': 300,
            'delay': 1,
            'json_path': 'Reservations[0].Instances[0].State.Name',
            'disrupted': 'shutting-down',
            'recovered': 'terminated',
            'configuration': configuration
        }

        tparams = {'instance_id': 'i-00000000000000000',
                   'configuration': configuration}
        terminate_instance(**tparams)
        results = monitor(**params)
        self.assertEqual(results['ctk:monitor_results'], 'success')

    def test_monitor_ec2_state(self):
        session = self.replay('test_monitor_ec2_state')
        configuration = {'aws_session': session, 'aws_region': 'us-east-1'}
        params = {
            'probe_name': 'instance_state',
            'probe_args': {
                'instance_ids': ['i-00000000000000000'],
                'state': 'terminated'
            },
            'timeout': 300,
            'delay': 1,
            'disrupted': False,
            'recovered': True,
            'configuration': configuration
        }

        tparams = {'instance_id': 'i-00000000000000000',
                   'configuration': configuration}
        terminate_instance(**tparams)
        results = monitor(**params)
        self.assertEqual(results['ctk:monitor_results'], 'success')
