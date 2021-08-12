from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "describe_cache_cluster",
    "get_cache_node_count",
    "get_cache_node_status",
    "count_cache_clusters_from_replication_group",
]


def describe_cache_cluster(
    cluster_id: str,
    show_node_info: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Returns cache cluster data for given cluster

    :param cluster_id: str: the name of the cache cluster
    :param show_node_info: bool: show associated nodes (default: False)
    :param configuration: Configuration
    :param secrets: Secrets

    :example:
    {
        "type": "probe",
        "name": "validate cache cluster engine",
        "tolerance": {
            "type": "jsonpath",
            "path": $.CacheClusters[0].Engine,
            "expect": "memcached"
        },
        "provider": {
            "type": "python",
            "module": "chaosaws.elasticache.probes",
            "func": "describe_cache_cluster",
            "arguments": {
                "cluster_id": "MyTestCluster"
            }
        }
    }

    Full list of possible paths can be found:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elasticache.html#ElastiCache.Client.describe_cache_clusters
    """
    params = dict(CacheClusterId=cluster_id, ShowCacheNodeInfo=show_node_info or False)
    client = aws_client("elasticache", configuration, secrets)

    try:
        response = client.describe_cache_clusters(**params)
        if not response.get("CacheClusters"):
            raise FailedActivity(
                "describe_cache_cluster failed: unable to "
                "find cache cluster with id: %s" % cluster_id
            )
        return response
    except ClientError as e:
        raise FailedActivity(
            "describe_cache_cluster failed: (%s) %s"
            % (e.response["Error"]["Code"], e.response["Error"]["Message"])
        )


def get_cache_node_count(
    cluster_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> int:
    """Returns the number of cache nodes associated to the cluster

    :param cluster_id: str: the name of the cache cluster
    :param configuration: Configuration
    :param secrets: Secrets

    :example:
    {
        "type": "probe",
        "name": "validate cache node count",
        "tolerance": 3,
        "provider": {
            "type": "python",
            "module": "chaosaws.elasticache.probes",
            "func": "get_cache_node_count",
            "arguments": {
                "cluster_id": "MyTestCluster"
            }
        }
    }
    """
    response = describe_cache_cluster(
        cluster_id, configuration=configuration, secrets=secrets
    )
    return response["CacheClusters"][0].get("NumCacheNodes", 0)


def get_cache_node_status(
    cluster_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> str:
    """Returns the status of the given cache cluster

    :param cluster_id: str: the name of the cache cluster
    :param configuration: Configuration
    :param secrets: Secrets

    :example:
    {
        "type": "probe",
        "name": "validate cache node status",
        "tolerance": "available",
        "provider": {
            "type": "python",
            "module": "chaosaws.elasticache.probes",
            "func": "get_cache_node_status",
            "arguments": {
                "cluster_id": "MyTestCluster"
            }
        }
    }

    """
    response = describe_cache_cluster(
        cluster_id, configuration=configuration, secrets=secrets
    )
    return response["CacheClusters"][0].get("CacheClusterStatus", "")


def count_cache_clusters_from_replication_group(
    replication_group_id: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """
    Returns the number of cache clusters that are part of the given
    ReplicationGroupId
    :param replication_group_id: The identifier for the replication group
    to be described
    :param configuration: Configuration
    :param secrets: Secrets
    Probe example:
        "steady-state-hypothesis": {
            "title": "MyCluster has 3 nodes",
            "probes": [{
                "type": "probe",
                "name": "Cluster running node count",
                "tolerance": 3,
                "provider": {
                    "type": "python",
                    "module": "modules.elasticache",
                    "func": "count_cache_clusters_from_replication_group",
                    "arguments": {
                        "replication_group_id": "MyCluster"
                    }
                }
            }
        }
    """
    client = aws_client("elasticache", configuration=configuration, secrets=secrets)

    response = client.describe_replication_groups(
        ReplicationGroupId=replication_group_id
    )

    rep_groups = response.get("ReplicationGroups", [])
    if not rep_groups:
        raise FailedActivity(
            "Error retrieving ReplicationGroups for " "{}".format(replication_group_id)
        )

    return len(rep_groups[0].get("MemberClusters", []))
