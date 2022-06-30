from typing import List

from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.emr.shared import (
    describe_emr_cluster,
    get_instance_fleet,
    get_instance_group,
    list_emr_instances,
)
from chaosaws.types import AWSResponse

__all__ = [
    "describe_cluster",
    "describe_instance_fleet",
    "describe_instance_group",
    "list_cluster_fleet_instances",
    "list_cluster_group_instances",
]


def describe_cluster(
    cluster_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """Describe a single EMR cluster

    :param cluster_id: The cluster id
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)
    return describe_emr_cluster(client, cluster_id)


def describe_instance_fleet(
    cluster_id: str,
    fleet_id: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Describe a single EMR instance fleet

    :param cluster_id: The cluster id
    :param fleet_id: The instance fleet id
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)
    return get_instance_fleet(client, cluster_id, fleet_id)


def describe_instance_group(
    cluster_id: str,
    group_id: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Describe a single EMR instance group

    :param cluster_id: The cluster id
    :param group_id: The instance group id
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)
    return get_instance_group(client, cluster_id, group_id)


def list_cluster_group_instances(
    cluster_id: str,
    group_id: str,
    group_type: str = None,
    instance_states: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Get a list of instance group instances associated to the EMR cluster

    :param cluster_id: The cluster id
    :param group_id: The instance group id
    :param group_type: The instance group type
    :param instance_states: A list of instance states to include
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)
    return list_emr_instances(
        client=client,
        cluster_id=cluster_id,
        group_id=group_id,
        group_type=group_type,
        instance_states=instance_states,
    )


def list_cluster_fleet_instances(
    cluster_id: str,
    fleet_id: str,
    fleet_type: str = None,
    instance_states: List[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Get a list of instance fleet instances associated to the EMR cluster

    :param cluster_id: The cluster id
    :param fleet_id: The instance fleet id
    :param fleet_type: The instance fleet type
    :param instance_states: A list of instance states to include
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)
    return list_emr_instances(
        client=client,
        cluster_id=cluster_id,
        fleet_id=fleet_id,
        fleet_type=fleet_type,
        instance_states=instance_states,
    )


def list_emr_clusters(
    configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    client = aws_client("emr", configuration, secrets)
    clusters = client.list_clusters()
    for c in clusters:
        print(c)
    return clusters
