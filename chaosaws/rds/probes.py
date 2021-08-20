from typing import Any, Dict, List, Union

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["instance_status", "cluster_status", "cluster_membership_count"]


def instance_status(
    instance_id: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Union[str, List[str]]:
    if (not instance_id and not filters) or (instance_id and filters):
        raise FailedActivity("instance_id or filters are required")

    client = aws_client("rds", configuration, secrets)
    results = describe_db_instances(
        client=client, instance_id=instance_id, filters=filters
    )
    if not results:
        if instance_id:
            raise FailedActivity("no instance found matching %s" % instance_id)
        if filters:
            raise FailedActivity("no instance(s) found matching %s" % filters)

    # if all instances have the same status return only single value.
    # eg: "available"
    # if an instances has a different status, return list
    # eg: ["available", "creating"]
    results = list({r["DBInstanceStatus"] for r in results["DBInstances"]})
    if len(results) == 1:
        return results[0]
    return results


def cluster_status(
    cluster_id: str = None,
    filters: List[Dict[str, Any]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Union[str, List[str]]:
    if (not cluster_id and not filters) or (cluster_id and filters):
        raise FailedActivity("cluster_id or filters are required")

    client = aws_client("rds", configuration, secrets)
    results = describe_db_cluster(client=client, cluster_id=cluster_id, filters=filters)
    if not results:
        if cluster_id:
            raise FailedActivity("no cluster found matching %s" % cluster_id)
        if filters:
            raise FailedActivity("no cluster(s) found matching %s" % filters)

    # if all instances have the same status return only single value.
    # eg: "available"
    # if an instances has a different status, return list of unique values
    # eg: ["available", "backing-up"]
    results = list({r["Status"] for r in results["DBClusters"]})
    if len(results) == 1:
        return results[0]
    return results


def cluster_membership_count(
    cluster_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> int:
    client = aws_client("rds", configuration, secrets)
    results = describe_db_cluster(client=client, cluster_id=cluster_id)
    if not results:
        raise FailedActivity("no cluster found matching %s" % cluster_id)
    return len(results["DBClusters"][0]["DBClusterMembers"])


###############################################################################
# Private functions
###############################################################################
def describe_db_instances(
    client: boto3.client, instance_id: str = None, filters: List[Dict[str, Any]] = None
) -> AWSResponse:
    paginator = client.get_paginator("describe_db_instances")
    params = dict()

    if instance_id:
        params["DBInstanceIdentifier"] = instance_id
    if filters:
        params["Filters"] = filters

    results = {}
    for p in paginator.paginate(**params):
        results.setdefault("DBInstances", []).extend(p["DBInstances"])
    logger.info("found %s instances" % len(results["DBInstances"]))
    return results


def describe_db_cluster(
    client: boto3.client, cluster_id: str = None, filters: List[Dict[str, Any]] = None
) -> AWSResponse:
    paginator = client.get_paginator("describe_db_clusters")
    params = dict()

    if cluster_id:
        params["DBClusterIdentifier"] = cluster_id
    if filters:
        params["Filters"] = filters

    results = {}
    for p in paginator.paginate(**params):
        results.setdefault("DBClusters", []).extend(p["DBClusters"])
    logger.info("found %s clusters" % len(results["DBClusters"]))
    return results
