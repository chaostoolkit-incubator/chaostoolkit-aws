from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.elasticache.actions import (
    delete_cache_clusters,
    delete_replication_groups,
    reboot_cache_clusters,
)
from chaosaws.elasticache.actions import test_failover as failover


def test_reboot_cache_clusters_invalid():
    with pytest.raises(TypeError) as x:
        reboot_cache_clusters()
    assert (
        "reboot_cache_clusters() missing 1 required positional "
        "argument: 'cluster_ids'" in str(x.value)
    )


def test_delete_cache_clusters_no_cluster():
    with pytest.raises(TypeError) as x:
        delete_cache_clusters(final_snapshot_id="MyClusterFinalSnapshot")
    assert (
        "delete_cache_clusters() missing 1 required positional "
        "argument: 'cluster_ids'" in str(x.value)
    )


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_reboot_cache_clusters_select_nodes(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_ids = ["MyTestCacheCluster"]
    node_ids = ["0001", "0003"]

    client.describe_cache_clusters.return_value = {
        "CacheClusters": [
            {
                "CacheClusterId": "MyTestCacheCluster",
                "CacheNodes": [
                    {"CacheNodeId": "0001"},
                    {"CacheNodeId": "0002"},
                    {"CacheNodeId": "0003"},
                    {"CacheNodeId": "0004"},
                ],
            }
        ]
    }
    client.reboot_cache_cluster.return_value = {
        "CacheCluster": {
            "CacheClusterId": "MyTestCacheCluster",
            "CacheNodes": [
                {"CacheNodeId": "0001"},
                {"CacheNodeId": "0002"},
                {"CacheNodeId": "0003"},
                {"CacheNodeId": "0004"},
            ],
        }
    }

    results = reboot_cache_clusters(cluster_ids, node_ids)
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId=cluster_ids[0], ShowCacheNodeInfo=True
    )
    client.reboot_cache_cluster.assert_called_with(
        CacheClusterId=cluster_ids[0], CacheNodeIdsToReboot=node_ids
    )
    assert results[0]["CacheClusterId"] == cluster_ids[0]


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_reboot_cache_clusters_all_nodes(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_ids = ["MyTestCacheCluster"]

    client.describe_cache_clusters.return_value = {
        "CacheClusters": [
            {
                "CacheClusterId": "MyTestCacheCluster",
                "CacheNodes": [
                    {"CacheNodeId": "0001"},
                    {"CacheNodeId": "0002"},
                    {"CacheNodeId": "0003"},
                    {"CacheNodeId": "0004"},
                ],
            }
        ]
    }
    client.reboot_cache_cluster.return_value = {
        "CacheCluster": {
            "CacheClusterId": "MyTestCacheCluster",
            "CacheNodes": [
                {"CacheNodeId": "0001"},
                {"CacheNodeId": "0002"},
                {"CacheNodeId": "0003"},
                {"CacheNodeId": "0004"},
            ],
        }
    }

    results = reboot_cache_clusters(cluster_ids)
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId=cluster_ids[0], ShowCacheNodeInfo=True
    )
    client.reboot_cache_cluster.assert_called_with(
        CacheClusterId=cluster_ids[0],
        CacheNodeIdsToReboot=["0001", "0002", "0003", "0004"],
    )
    assert results[0]["CacheClusterId"] == cluster_ids[0]


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_delete_cache_clusters_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    client.describe_cache_clusters.return_value = {
        "CacheClusters": [
            {
                "CacheClusterId": "MyTestCacheCluster",
                "CacheClusterStatus": "available",
                "CacheNodes": [
                    {"CacheNodeId": "0001"},
                    {"CacheNodeId": "0002"},
                ],
            }
        ]
    }
    client.delete_cache_cluster.return_value = {
        "CacheCluster": {
            "CacheClusterId": "MyTestCacheCluster",
            "CacheClusterStatus": "snapshotting",
            "CacheNodes": [{"CacheNodeId": "0001"}, {"CacheNodeId": "0002"}],
        }
    }

    results = delete_cache_clusters(
        cluster_ids=["MyTestCacheCluster"],
        final_snapshot_id="MyClusterFinalSnap",
    )
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=True
    )
    client.delete_cache_cluster.assert_called_with(
        CacheClusterId="MyTestCacheCluster",
        FinalSnapshotIdentifier="MyClusterFinalSnap",
    )
    assert results[0]["CacheClusterId"] == "MyTestCacheCluster"
    assert results[0]["CacheClusterStatus"] == "snapshotting"


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_delete_cache_clusters_no_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    client.describe_cache_clusters.return_value = {
        "CacheClusters": [
            {
                "CacheClusterId": "MyTestCacheCluster",
                "CacheClusterStatus": "available",
                "CacheNodes": [
                    {"CacheNodeId": "0001"},
                    {"CacheNodeId": "0002"},
                ],
            }
        ]
    }
    client.delete_cache_cluster.return_value = {
        "CacheCluster": {
            "CacheClusterId": "MyTestCacheCluster",
            "CacheClusterStatus": "deleting",
            "CacheNodes": [{"CacheNodeId": "0001"}, {"CacheNodeId": "0002"}],
        }
    }

    results = delete_cache_clusters(cluster_ids=["MyTestCacheCluster"])
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=True
    )
    client.delete_cache_cluster.assert_called_with(
        CacheClusterId="MyTestCacheCluster"
    )
    assert results[0]["CacheClusterId"] == "MyTestCacheCluster"
    assert results[0]["CacheClusterStatus"] == "deleting"


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_delete_replication_group_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    group_ids = ["MyRedisReplicationGroup"]
    final_snapshot_id = "MyReplicationGroupFinalSnap"

    client.describe_replication_groups.return_value = {
        "ReplicationGroups": [
            {"ReplicationGroupId": group_ids[0], "Status": "available"}
        ]
    }
    client.delete_replication_group.return_value = {
        "ReplicationGroup": {
            "ReplicationGroupId": group_ids[0],
            "Status": "snapshotting",
        }
    }

    results = delete_replication_groups(
        group_ids=group_ids, final_snapshot_id=final_snapshot_id
    )

    client.describe_replication_groups.assert_called_with(
        ReplicationGroupId=group_ids[0]
    )
    client.delete_replication_group.assert_called_with(
        ReplicationGroupId=group_ids[0],
        RetainPrimaryCluster=True,
        FinalSnapshotIdentifier=final_snapshot_id,
    )

    assert results[0]["ReplicationGroupId"] == group_ids[0]
    assert results[0]["Status"] == "snapshotting"


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_delete_replication_group_no_snapshot(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    group_ids = ["MyRedisReplicationGroup"]

    client.describe_replication_groups.return_value = {
        "ReplicationGroups": [
            {"ReplicationGroupId": group_ids[0], "Status": "available"}
        ]
    }
    client.delete_replication_group.return_value = {
        "ReplicationGroup": {
            "ReplicationGroupId": group_ids[0],
            "Status": "deleting",
        }
    }

    results = delete_replication_groups(group_ids=group_ids)

    client.describe_replication_groups.assert_called_with(
        ReplicationGroupId=group_ids[0]
    )
    client.delete_replication_group.assert_called_with(
        ReplicationGroupId=group_ids[0], RetainPrimaryCluster=True
    )

    assert results[0]["ReplicationGroupId"] == group_ids[0]
    assert results[0]["Status"] == "deleting"


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_failover(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    replication_group_id = "my-redis-rg"
    node_group_id = "0001"
    failover(replication_group_id, node_group_id)
    client.test_failover.assert_called_with(
        ReplicationGroupId=replication_group_id, NodeGroupId=node_group_id
    )


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_failover_missing_required_params(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    replication_group_id = ""
    node_group_id = ""

    with pytest.raises(FailedActivity):
        failover(replication_group_id, node_group_id)


@patch("chaosaws.elasticache.actions.aws_client", autospec=True)
def test_failover_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    replication_group_id = "my-redis-rg"
    node_group_id = "0001"

    with patch.object(client, "test_failover", FailedActivity):
        with pytest.raises(Exception):
            failover(replication_group_id, node_group_id)
