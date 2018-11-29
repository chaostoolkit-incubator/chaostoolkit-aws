# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.rds.actions import (failover_db_cluster,
                                  reboot_db_instance)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_failover_db_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = 'my-db-cluster-identifier'
    failover_db_cluster(db_cluster_identifier)
    client.failover_db_cluster.assert_called_with(
        DBClusterIdentifier=db_cluster_identifier,
        TargetDBInstanceIdentifier=None)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_failover_db_cluster_with_instance_identifier(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = 'my-db-cluser-identifier'
    target_db_instance_identifer = 'my-target-instance-identifier'
    failover_db_cluster(db_cluster_identifier, target_db_instance_identifer)
    client.failover_db_cluster.assert_called_with(
        DBClusterIdentifier=db_cluster_identifier,
        TargetDBInstanceIdentifier=target_db_instance_identifer)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_failover_db_cluster_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = ''
    with pytest.raises(FailedActivity):
        failover_db_cluster(db_cluster_identifier)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_failover_db_cluster_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = 'my-db-cluster-identifier'

    with patch.object(client, 'failover_db_cluster', FailedActivity):
        with pytest.raises(Exception):
            failover_db_cluster(db_cluster_identifier)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_reboot_db_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = 'my-db-instance-identifier'
    reboot_db_instance(db_instance_identifier)
    client.reboot_db_instance.assert_called_with(
        DBInstanceIdentifier=db_instance_identifier,
        ForceFailover=False)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_reboot_db_instance_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = ''
    with pytest.raises(FailedActivity):
        reboot_db_instance(db_instance_identifier)


@patch('chaosaws.rds.actions.aws_client', autospec=True)
def test_reboot_db_instance_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = 'my-db-instance-identifier'

    with patch.object(client, 'reboot_db_instance', FailedActivity):
        with pytest.raises(Exception):
            reboot_db_instance(db_instance_identifier)
