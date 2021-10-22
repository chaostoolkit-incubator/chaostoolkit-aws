from typing import Any, Dict, List

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "reboot_cache_clusters",
    "delete_cache_clusters",
    "delete_replication_groups",
    "test_failover",
]


def reboot_cache_clusters(
    cluster_ids: List[str],
    node_ids: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Reboots one or more nodes in a cache cluster.
    If no node ids are supplied, all nodes in the cluster will be rebooted

    Parameters:
        cluster_ids: list: a list of one or more cache cluster ids
        node_ids: list: a list of one or more node ids in to the cluster
    """
    client = aws_client("elasticache", configuration, secrets)
    cache_clusters = describe_cache_clusters(cluster_ids, client)

    results = []
    for c in cache_clusters:
        node_ids = validate_cluster_nodes(c, node_ids)
        results.append(
            client.reboot_cache_cluster(
                CacheClusterId=c["CacheClusterId"], CacheNodeIdsToReboot=node_ids
            )["CacheCluster"]
        )
    return results


def delete_cache_clusters(
    cluster_ids: List[str],
    final_snapshot_id: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Deletes one or more cache clusters and creates a final snapshot

    Parameters:
         cluster_ids: list: a list of one or more cache cluster ids
         final_snapshot_id: str: an identifier to give the final snapshot
    """
    client = aws_client("elasticache", configuration, secrets)
    cache_clusters = describe_cache_clusters(cluster_ids, client)

    results = []
    for c in cache_clusters:
        logger.debug("Deleting Cache Cluster: %s." % c["CacheClusterId"])

        params = dict(CacheClusterId=c["CacheClusterId"])
        if final_snapshot_id:
            params["FinalSnapshotIdentifier"] = final_snapshot_id
        results.append(client.delete_cache_cluster(**params)["CacheCluster"])
    return results


def delete_replication_groups(
    group_ids: List[str],
    final_snapshot_id: str = None,
    retain_primary_cluster: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Deletes one or more replication groups and creates a final snapshot

    Parameters:
        group_ids: list: a list of one or more replication group ids
        final_snapshot_id: str: an identifier to give the final snapshot
        retain_primary_cluster: bool (default: True): delete only the read
            replicas associated to the replication group, not the primary
    """
    client = aws_client("elasticache", configuration, secrets)
    replication_groups = describe_replication_groups(group_ids, client)

    results = []
    for r in replication_groups:
        logger.debug("Deleting Replication Group: %s" % (r["ReplicationGroupId"]))
        if retain_primary_cluster:
            logger.debug("Deleting only read replicas.")

        params = dict(
            ReplicationGroupId=r["ReplicationGroupId"],
            RetainPrimaryCluster=retain_primary_cluster,
        )

        if final_snapshot_id:
            params["FinalSnapshotIdentifier"] = final_snapshot_id

        results.append(client.delete_replication_group(**params)["ReplicationGroup"])
    return results


def test_failover(
    replication_group_id: str,
    node_group_id: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Tests automatic failover on a single shard (also known as node groups).
    You can only invoke test_failover for no more than 5 shards in any rolling 24-hour
    period.

    Parameters:
        replication_group_id: str: the name of the replication group
            (also known as cluster) whose automatic failover is being
            tested by this operation.
        node_group_id: str: the name of the node group (also known as shard)
            in this replication group on which automatic failover is to be tested.
    """
    client = aws_client("elasticache", configuration, secrets)

    if not (replication_group_id and node_group_id):
        raise FailedActivity(
            "you must specify the replication group id and node group id"
        )

    try:
        return client.test_failover(
            ReplicationGroupId=replication_group_id, NodeGroupId=node_group_id
        )
    except Exception as e:
        raise FailedActivity(
            f"failed invoking the test failover API for replication group "
            f"'{replication_group_id}' and node group '{node_group_id}': '{str(e)}'"
        ) from e


###############################################################################
# Private functions
###############################################################################
def describe_cache_clusters(
    cluster_ids: List[str], client: boto3.client
) -> List[AWSResponse]:
    results = []
    for c in cluster_ids:
        response = client.describe_cache_clusters(
            CacheClusterId=c, ShowCacheNodeInfo=True
        )["CacheClusters"]

        if not response:
            raise FailedActivity("Cache cluster %s not found." % c)

        for r in response:
            results.append(r)
    return results


def describe_replication_groups(
    group_ids: List[str], client: boto3.client
) -> List[AWSResponse]:
    results = []
    for g in group_ids:
        response = client.describe_replication_groups(ReplicationGroupId=g)[
            "ReplicationGroups"
        ]

        if not response:
            raise FailedActivity("Replication group %s not found." % g)

        for r in response:
            results.append(r)
    return results


def validate_cluster_nodes(
    cache_cluster: Dict[str, Any], node_ids: List[str] = None
) -> List[str]:
    missing_nodes = []
    actual_nodes = [n["CacheNodeId"] for n in cache_cluster["CacheNodes"]]
    if not node_ids:
        return actual_nodes

    for n in node_ids:
        if n not in actual_nodes:
            missing_nodes.append(n)

    if missing_nodes:
        raise FailedActivity(
            "Cache Cluster %s has no node(s) matching: %s"
            % (cache_cluster["CacheClusterId"], missing_nodes)
        )
    return node_ids
