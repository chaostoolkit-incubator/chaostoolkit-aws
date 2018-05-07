# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

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
