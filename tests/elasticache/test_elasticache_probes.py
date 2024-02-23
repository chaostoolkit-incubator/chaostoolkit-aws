from unittest.mock import MagicMock, patch

import pytest

from chaosaws.elasticache.probes import (
    count_cache_clusters_from_replication_group,
    describe_cache_cluster,
    get_cache_node_count,
    get_cache_node_status,
)

TestClusterFrame = {
    "CacheClusters": [
        {
            "CacheClusterId": "MyTestCacheCluster",
            "CacheClusterStatus": "available",
            "Engine": "memcached",
            "NumCacheNodes": 1,
        }
    ]
}

NodeInfoFrame = [
    {
        "CacheNodeId": "0001",
        "CacheNodeStatus": "available",
        "ParameterGroupStatus": "in-sync",
    }
]


def test_describe_elasticache_invalid():
    with pytest.raises(TypeError) as x:
        describe_cache_cluster()
    assert (
        "describe_cache_cluster() missing 1 required positional "
        "argument: 'cluster_id'" in str(x.value)
    )


def test_get_node_status_invalid():
    with pytest.raises(TypeError) as x:
        get_cache_node_status()
    assert (
        "get_cache_node_status() missing 1 required positional "
        "argument: 'cluster_id'" in str(x.value)
    )


def test_get_node_count_invalid():
    with pytest.raises(TypeError) as x:
        get_cache_node_count()
    assert (
        "get_cache_node_count() missing 1 required positional "
        "argument: 'cluster_id'" in str(x.value)
    )


def test_count_cache_clusters_from_replication_group():
    with pytest.raises(TypeError) as x:
        count_cache_clusters_from_replication_group()
    assert (
        "count_cache_clusters_from_replication_group() missing 1 "
        "required positional argument: 'replication_group_id'" in str(x.value)
    )


@patch("chaosaws.elasticache.probes.aws_client", autospec=True)
def test_describe_cache_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    client.describe_cache_clusters.return_value = TestClusterFrame
    response = describe_cache_cluster(cluster_id="MyTestCacheCluster")
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=False
    )
    assert (
        response["CacheClusters"][0]["CacheClusterId"] == "MyTestCacheCluster"
    )


@patch("chaosaws.elasticache.probes.aws_client", autospec=True)
def test_describe_cache_cluster_show_node_info(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    TestClusterFrame["CacheClusters"][0]["CacheNodes"] = NodeInfoFrame
    client.describe_cache_clusters.return_value = TestClusterFrame
    response = describe_cache_cluster(
        cluster_id="MyTestCacheCluster", show_node_info=True
    )

    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=True
    )
    assert (
        response["CacheClusters"][0]["CacheNodes"][0]["CacheNodeStatus"]
        == "available"
    )


@patch("chaosaws.elasticache.probes.aws_client", autospec=True)
def test_get_node_status(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    client = MagicMock()
    aws_client.return_value = client

    client.describe_cache_clusters.return_value = TestClusterFrame
    response = get_cache_node_status(cluster_id="MyTestCacheCluster")
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=False
    )
    assert response == "available"


@patch("chaosaws.elasticache.probes.aws_client", autospec=True)
def test_get_node_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    client = MagicMock()
    aws_client.return_value = client

    client.describe_cache_clusters.return_value = TestClusterFrame
    response = get_cache_node_count(cluster_id="MyTestCacheCluster")
    client.describe_cache_clusters.assert_called_with(
        CacheClusterId="MyTestCacheCluster", ShowCacheNodeInfo=False
    )
    assert response == 1
