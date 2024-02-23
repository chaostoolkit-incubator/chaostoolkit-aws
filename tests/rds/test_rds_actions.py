from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.rds.actions import (
    delete_db_cluster,
    delete_db_cluster_endpoint,
    delete_db_instance,
    failover_db_cluster,
    reboot_db_instance,
    stop_db_cluster,
    stop_db_instance,
)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_failover_db_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = "my-db-cluster-identifier"
    failover_db_cluster(db_cluster_identifier)
    client.failover_db_cluster.assert_called_with(
        DBClusterIdentifier=db_cluster_identifier,
        TargetDBInstanceIdentifier=None,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_failover_db_cluster_with_instance_identifier(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = "my-db-cluser-identifier"
    target_db_instance_identifer = "my-target-instance-identifier"
    failover_db_cluster(db_cluster_identifier, target_db_instance_identifer)
    client.failover_db_cluster.assert_called_with(
        DBClusterIdentifier=db_cluster_identifier,
        TargetDBInstanceIdentifier=target_db_instance_identifer,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_failover_db_cluster_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = ""
    with pytest.raises(FailedActivity):
        failover_db_cluster(db_cluster_identifier)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_failover_db_cluster_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_cluster_identifier = "my-db-cluster-identifier"

    with patch.object(client, "failover_db_cluster", FailedActivity):
        with pytest.raises(Exception):
            failover_db_cluster(db_cluster_identifier)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_reboot_db_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = "my-db-instance-identifier"
    reboot_db_instance(db_instance_identifier)
    client.reboot_db_instance.assert_called_with(
        DBInstanceIdentifier=db_instance_identifier, ForceFailover=False
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_reboot_db_instance_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = ""
    with pytest.raises(FailedActivity):
        reboot_db_instance(db_instance_identifier)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_reboot_db_instance_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_instance_identifier = "my-db-instance-identifier"

    with patch.object(client, "reboot_db_instance", FailedActivity):
        with pytest.raises(Exception):
            reboot_db_instance(db_instance_identifier)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_stop_db_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_id = "some-rds-instance-identifier"
    stop_db_instance(db_instance_identifier=db_id)
    client.stop_db_instance.assert_called_with(DBInstanceIdentifier=db_id)


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_stop_db_instance_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_id = "some-rds-instance-identifier"
    ss_id = "some-rds-snapshot-identifier"
    stop_db_instance(db_instance_identifier=db_id, db_snapshot_identifier=ss_id)
    client.stop_db_instance.assert_called_with(
        DBInstanceIdentifier=db_id, DBSnapshotIdentifier=ss_id
    )


def test_stop_db_instance_exception():
    with pytest.raises(TypeError) as x:
        stop_db_instance()
    assert (
        "stop_db_instance() missing 1 required positional argument: "
        "'db_instance_identifier'" in str(x.value)
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_stop_db_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_id = "some-aurora-cluster-identifier"
    stop_db_cluster(db_cluster_identifier=cluster_id)
    client.stop_db_cluster.assert_called_with(DBClusterIdentifier=cluster_id)


def test_stop_db_cluster_exception():
    with pytest.raises(TypeError) as x:
        stop_db_cluster()
    assert (
        "stop_db_cluster() missing 1 required positional argument: "
        "'db_cluster_identifier'" in str(x.value)
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_id = "some-rds-instance-identifier"
    delete_db_instance(
        db_instance_identifier=db_id,
        skip_final_snapshot=False,
        db_snapshot_identifier="%s-final-snapshot" % db_id,
    )

    client.delete_db_instance.assert_called_with(
        DBInstanceIdentifier=db_id,
        SkipFinalSnapshot=False,
        DeleteAutomatedBackups=True,
        FinalDBSnapshotIdentifier="%s-final-snapshot" % db_id,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_instance_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_id = "some-rds-instance-identifier"
    ss_id = "some-rds-snapshot-identifier"
    delete_db_instance(
        db_instance_identifier=db_id,
        skip_final_snapshot=False,
        db_snapshot_identifier=ss_id,
    )

    client.delete_db_instance.assert_called_with(
        DBInstanceIdentifier=db_id,
        SkipFinalSnapshot=False,
        DeleteAutomatedBackups=True,
        FinalDBSnapshotIdentifier=ss_id,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_instance_no_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    db_id = "some-rds-instance-identifier"
    delete_db_instance(db_instance_identifier=db_id)

    client.delete_db_instance.assert_called_with(
        DBInstanceIdentifier=db_id,
        SkipFinalSnapshot=True,
        DeleteAutomatedBackups=True,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_id = "some-aurora-identifier"
    delete_db_cluster(
        db_cluster_identifier=cluster_id,
        skip_final_snapshot=False,
        db_snapshot_identifier="%s-final-snapshot" % cluster_id,
    )

    client.delete_db_cluster.assert_called_with(
        DBClusterIdentifier=cluster_id,
        SkipFinalSnapshot=False,
        FinalDBSnapshotIdentifier="%s-final-snapshot" % cluster_id,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_cluster_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_id = "some-aurora-identifier"
    snapshot_id = "some-aurora-snapshot-identifier"
    delete_db_cluster(
        db_cluster_identifier=cluster_id,
        db_snapshot_identifier=snapshot_id,
        skip_final_snapshot=False,
    )

    client.delete_db_cluster.assert_called_with(
        DBClusterIdentifier=cluster_id,
        SkipFinalSnapshot=False,
        FinalDBSnapshotIdentifier=snapshot_id,
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_cluster_no_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_id = "some-aurora-identifier"
    delete_db_cluster(
        db_cluster_identifier=cluster_id, skip_final_snapshot=True
    )

    client.delete_db_cluster.assert_called_with(
        DBClusterIdentifier=cluster_id, SkipFinalSnapshot=True
    )


@patch("chaosaws.rds.actions.aws_client", autospec=True)
def test_delete_db_cluster_endpoint(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_id = "some-aurora-identifier"

    client.describe_db_clusters.return_value = {
        "DBClusters": [
            {
                "DBClusterIdentifier": cluster_id,
                "Endpoint": "%s.domain.endpoint" % cluster_id,
            }
        ]
    }

    delete_db_cluster_endpoint(db_cluster_identifier=cluster_id)
    client.delete_db_cluster_endpoint.assert_called_with(
        DBClusterEndpointIdentifier="%s.domain.endpoint" % cluster_id
    )
