from typing import List

from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.emr.shared import get_instance_fleet, get_instance_group
from chaosaws.types import AWSResponse

__all__ = [
    "modify_cluster",
    "modify_instance_fleet",
    "modify_instance_groups_instance_count",
    "modify_instance_groups_shrink_policy",
]


def modify_cluster(
    cluster_id: str,
    concurrency: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Set the step concurrency level on the provided cluster

    :param cluster_id: The cluster id
    :param concurrency: The number of steps to execute concurrently (1 - 256)
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)

    try:
        return client.modify_cluster(
            ClusterId=cluster_id, StepConcurrencyLevel=concurrency
        )
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def modify_instance_fleet(
    cluster_id: str,
    fleet_id: str,
    on_demand_capacity: int = None,
    spot_capacity: int = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Modify the on-demand and spot capacities for an instance fleet

    :param cluster_id: The cluster id
    :param fleet_id: The instance fleet id
    :param on_demand_capacity: Target capacity of on-demand units
    :param spot_capacity: Target capacity of spot units
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    if not any([on_demand_capacity, spot_capacity]):
        raise FailedActivity(
            "Must provide at least one of " '["on_demand_capacity", "spot_capacity"]'
        )

    client = aws_client("emr", configuration, secrets)

    params = {
        "ClusterId": cluster_id,
        "InstanceFleet": {
            "InstanceFleetId": fleet_id,
            **({"TargetSpotCapacity": spot_capacity} if spot_capacity else {}),
            **(
                {"TargetOnDemandCapacity": on_demand_capacity}
                if on_demand_capacity
                else {}
            ),
        },
    }

    try:
        client.modify_instance_fleet(**params)
        return get_instance_fleet(client, cluster_id, fleet_id)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def modify_instance_groups_instance_count(
    cluster_id: str,
    group_id: str,
    instance_count: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Modify the number of instances in an instance group

    :param cluster_id: The cluster id
    :param group_id: The instance group id
    :param instance_count: The target size for the instance group
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("emr", configuration, secrets)

    try:
        client.modify_instance_groups(
            ClusterId=cluster_id,
            InstanceGroups=[
                {"InstanceGroupId": group_id, "InstanceCount": instance_count}
            ],
        )
        return get_instance_group(client, cluster_id, group_id)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def modify_instance_groups_shrink_policy(
    cluster_id: str,
    group_id: str,
    decommission_timeout: int = None,
    terminate_instances: List[str] = None,
    protect_instances: List[str] = None,
    termination_timeout: int = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """Modify an instance groups shrink operations

    :param cluster_id: The cluster id
    :param group_id: The instance group id
    :param decommission_timeout: Timeout for decommissioning an instance
    :param terminate_instances: Instance id list to terminate when shrinking
    :param protect_instances: Instance id list to protect when shrinking
    :param termination_timeout: Override for list of instances to terminate
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    if not any([decommission_timeout, terminate_instances, protect_instances]):
        raise FailedActivity(
            "Must provide at least one of ["
            '"decommission_timeout", "terminate_instances",'
            '"protect_instances"]'
        )

    if termination_timeout and not terminate_instances:
        raise FailedActivity(
            'Must provide "terminate_instances" when '
            'specifying "termination_timeout"'
        )

    resize_policy = {
        **(
            {"InstancesToTerminate": terminate_instances} if terminate_instances else {}
        ),
        **({"InstancesToProtect": protect_instances} if protect_instances else {}),
        **(
            {"InstanceTerminationTimeout": termination_timeout}
            if termination_timeout
            else {}
        ),
    }

    params = {
        "ClusterId": cluster_id,
        "InstanceGroups": [
            {
                "InstanceGroupId": group_id,
                "ShrinkPolicy": {
                    **(
                        {"DecommissionTimeout": decommission_timeout}
                        if decommission_timeout
                        else {}
                    ),
                    **(
                        {"InstanceResizePolicy": resize_policy} if resize_policy else {}
                    ),
                },
            }
        ],
    }

    client = aws_client("emr", configuration, secrets)

    try:
        client.modify_instance_groups(**params)
        return get_instance_group(client, cluster_id, group_id)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])
