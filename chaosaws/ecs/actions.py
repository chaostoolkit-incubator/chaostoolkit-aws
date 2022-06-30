import random
import re
from typing import Dict, List, Union

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "stop_random_tasks",
    "stop_task",
    "delete_service",
    "tag_resource",
    "delete_cluster",
    "deregister_container_instance",
    "untag_resource",
    "update_desired_count",
    "set_service_placement_strategy",
    "set_service_deployment_configuration",
    "update_container_instances_state",
]


def stop_random_tasks(
    cluster: str,
    task_count: int = None,
    task_percent: int = None,
    service: str = None,
    reason: str = "Chaos Testing",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Stop a random number of tasks based on given task_count or task_percent

    You can specify a cluster by its ARN identifier or, if not provided, the
    default cluster will be picked up.

    :param cluster: The ECS cluster Name
    :param task_count: The number of tasks to stop
    :param task_percent: The percentage of total tasks to stop
    :param service: The ECS service name
    :param reason: An explanation of why the service was stopped
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: List[Dict[str, Any]]
    """
    if not any([task_count, task_percent]) or all([task_count, task_percent]):
        raise FailedActivity('Must specify one of "task_count", "task_percent"')

    client = aws_client("ecs", configuration, secrets)
    validate(client, cluster, service)

    tasks = list_running_tasks_in_cluster(
        cluster=cluster, client=client, service=service
    )

    if task_percent:
        task_count = int(float(len(tasks) * float(task_percent)) / 100)

    if len(tasks) < task_count:
        raise FailedActivity(
            "Not enough running tasks in {} to satisfy "
            "stop count {} ({})".format(cluster, task_count, len(tasks))
        )

    tasks = random.sample(tasks, task_count)

    results = []
    for task in tasks:
        logger.debug(f"Stopping ECS task: {task}")
        response = client.stop_task(cluster=cluster, task=task, reason=reason)
        results.append(
            {
                "Task_Id": response["task"]["taskArn"],
                "Desired_Status": response["task"]["desiredStatus"],
            }
        )
    return results


def stop_task(
    cluster: str = None,
    task_id: str = None,
    service: str = None,
    reason: str = "Chaos Testing",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Stop a given ECS task instance. If no task_id provided, a random task of
    the given service is stopped.
    You can specify a cluster by its ARN identifier or, if not provided, the
    default cluster will be picked up.
    """
    client = aws_client("ecs", configuration, secrets)
    if not task_id and service:
        tasks = list_tasks(cluster=cluster, client=client, service=service)
        if not tasks:
            raise FailedActivity(f"No ECS tasks found for service: {service}")
        task_id = random.choice(tasks)
        task_id = task_id.rsplit("/", 1)[1]

    logger.debug(f"Stopping ECS task: {task_id}")
    return client.stop_task(cluster=cluster, task=task_id, reason=reason)


def delete_service(
    service: str = None,
    cluster: str = None,
    service_pattern: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Update a given ECS service by updating it to set the desired count of tasks
    to 0 then delete it. If not provided, a random one will be picked up
    regarding `service_pattern`, if provided, so that only service names
    matching the pattern would be be used. This should be a valid regex.

    You can specify a cluster by its ARN identifier or, if not provided, the
    default cluster will be picked up.
    """
    client = aws_client("ecs", configuration, secrets)
    if not service:
        services = list_services_arns(cluster=cluster, client=client)
        if not services:
            raise FailedActivity(f"No ECS services found in cluster: {cluster}")

        # should we filter the number of services to take into account?
        if service_pattern:
            services = filter_services(services=services, pattern=service_pattern)
            if not services:
                raise FailedActivity(
                    f"No ECS services matching pattern: {service_pattern}"
                )

        service = random.choice(services)
        service = service.rsplit("/", 1)[1]

    logger.debug(f"Updating ECS service: {service}")
    client.update_service(
        cluster=cluster,
        service=service,
        desiredCount=0,
        deploymentConfiguration={"maximumPercent": 100, "minimumHealthyPercent": 0},
    )

    logger.debug(f"Deleting ECS service: {service}")
    return client.delete_service(cluster=cluster, service=service)


def delete_cluster(
    cluster: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Delete an ECS cluster

    :param cluster: The ECS cluster name or ARN
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("ecs", configuration, secrets)
    logger.debug(f"Deleting ECS cluster: {cluster}")
    return client.delete_cluster(cluster=cluster)


def deregister_container_instance(
    cluster: str,
    instance_id: str,
    force: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Deregister an ECS container

    Warning: If using "force", Any tasks not deleted before deregistration
    will remain orphaned

    :param cluster: The ECS cluster name or ARN or ARN
    :param instance_id: The container instance id or ARN
    :param force: Force deregistraion of container instance
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("ecs", configuration, secrets)
    logger.debug(
        "Deregistering container instance '{}' from ECS cluster: {}".format(
            instance_id, cluster
        )
    )
    return client.deregister_container_instance(
        cluster=cluster, containerInstance=instance_id, force=force
    )


def update_desired_count(
    cluster: str,
    service: str,
    desired_count: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Set the number of desired tasks for an ECS service

    :param cluster: The ECS cluster name or ARN or ARN
    :param service: The ECS service name
    :param desired_count: The number of instantiation of the tasks to run
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]

    Example:
        "method": {
            "type": "action",
            "name": "update service",
            "provider": {
                "type": "python",
                "module": "chaosaws.ecs.actions",
                "func": "update_desired_count",
                "arguments": {
                    "cluster": "my_cluster_name",
                    "service": "my_service_name",
                    "desired_count": 6
                }
            }
        }
    """
    client = aws_client("ecs", configuration, secrets)
    validate(client, cluster, service)

    return client.update_service(
        cluster=cluster, service=service, desiredCount=desired_count
    )


def set_service_deployment_configuration(
    cluster: str,
    service: str,
    maximum_percent: int = 200,
    minimum_healthy_percent: int = 100,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Sets the maximum healthy count and minimum healthy percentage values for
    a services deployment configuration

    :param cluster: The ECS cluster name or ARN
    :param service: The ECS service name
    :param maximum_percent: The upper limit on the number of tasks a service is
        allowed to have in RUNNING or PENDING during deployment
    :param minimum_healthy_percent: The lower limit on the number of tasks a
        service must keep in RUNNING to be considered healthy during deployment
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    if minimum_healthy_percent > maximum_percent:
        raise FailedActivity(
            "minimum_healthy_percent cannot be larger " "than maximum_percent"
        )

    client = aws_client("ecs", configuration, secrets)

    if not validate_cluster(cluster, client):
        raise FailedActivity("unable to locate cluster: %s" % cluster)
    if not validate_service(cluster, service, client):
        raise FailedActivity(f"unable to locate service: {service} on {cluster}")

    params = {
        "cluster": cluster,
        "service": service,
        "deploymentConfiguration": {
            "maximumPercent": maximum_percent,
            "minimumHealthyPercent": minimum_healthy_percent,
        },
    }
    return client.update_service(**params)


def set_service_placement_strategy(
    cluster: str,
    service: str,
    placement_type: str,
    placement_field: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Sets the service's instance placement strategy

    :param cluster: The ECS cluster name or ARN
    :param service: The ECS service name
    :param placement_type: The type of placement strategy to employ
        (random, spread, or binpack)
    :param placement_field: The field to apply the strategy against
        (eg: "attribute:ecs.availability-zone")
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    if placement_type in ("spread", "binpack") and not placement_field:
        raise FailedActivity(
            '"placement_field" is required when using ' '"spread" or "binpack"'
        )

    client = aws_client("ecs", configuration, secrets)
    validate(client, cluster, service)

    if placement_type == "random":
        placement_field = None

    params = {
        "cluster": cluster,
        "service": service,
        "placementStrategy": [
            {
                "type": placement_type,
                **({"field": placement_field} if placement_field else {}),
            }
        ],
    }

    try:
        return client.update_service(**params)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def tag_resource(
    tags: List[Dict[str, str]],
    resource_arn: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Tags the provided resource(s) with provided tags

    ** For ECS resources, the long form ARN must be used
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-account-settings.html#ecs-resource-arn-timeline

    Example:
        {
            "tags": [
                {"key": "MyTagKey", "value": "MyTagValue"},
                {"key": "MyOtherTagKey", "value": "MyOtherTagValue"}
            ],
            "resource_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/name"
        }

    :param tags: A list of key/value pairs
    :param resource_arn: The ARN of the resource to tag.
        Valid resources: capacity providers, tasks, services, task definitions,
        clusters, and container instances
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("ecs", configuration, secrets)
    try:
        client.tag_resource(resourceArn=resource_arn, tags=tags)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def untag_resource(
    tag_keys: List[str],
    resource_arn: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Removes the given tags from the provided resource

    ** For ECS resources, the long form ARN must be used
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-account-settings.html#ecs-resource-arn-timeline

    Example:
        {
            "tag_keys": ["MyTagKey", "MyOtherTagKey"],
            "resource_arn": "arn:aws:ecs:...:service/cluster-name/service-name"
        }

    :param tag_keys: A list of tag keys to remove
    :param resource_arn: The ARN of the resource to tag.
        Valid resources: capacity providers, tasks, services, task definitions,
        clusters, and container instances
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("ecs", configuration, secrets)
    try:
        client.untag_resource(resourceArn=resource_arn, tagKeys=tag_keys)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def update_container_instances_state(
    cluster: str,
    container_instances: List[str],
    status: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Modify the status of an ACTIVE ECS container instance

    :param cluster: The ECS cluster name or ARN
    :param container_instances: A list of container instance ids for ARNs
    :param status: The desired instance state (Valid States: ACTIVE, DRAINING)
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: Dict[str, Any]
    """
    client = aws_client("ecs", configuration, secrets)
    validate(client, cluster)

    try:
        return client.update_container_instance_state(
            cluster=cluster, containerInstances=container_instances, status=status
        )
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


###############################################################################
# Private functions
###############################################################################
def validate(client: boto3.client, cluster: str = None, service: str = None):
    """Validate that a service and/or cluster exists"""
    if cluster:
        response = client.describe_clusters(clusters=[cluster])["clusters"]
        if not response:
            raise FailedActivity("unable to locate cluster: %s" % cluster)

    if service:
        response = client.describe_services(cluster=cluster, services=[service])[
            "services"
        ]
        if not response:
            raise FailedActivity(
                f"unable to locate service: {service} on cluster: {cluster}"
            )


def validate_cluster(cluster: str, client: boto3.client) -> Union[str, None]:
    """Validates the provided cluster exists"""
    cluster = client.describe_clusters(clusters=[cluster])["clusters"]
    if not cluster:
        return
    return cluster[0]["clusterArn"]


def validate_service(
    cluster: str, service: str, client: boto3.client
) -> Union[str, None]:
    """Validates the provided service exists in the cluster"""
    service = client.describe_services(cluster=cluster, services=[service])["services"]
    if not service:
        return
    return service[0]["serviceArn"]


def list_services_arns(cluster: str, client: boto3.client) -> List[str]:
    """Return of all services arns in the given cluster."""
    services = []

    def _list(next_token=None):
        params = {
            "cluster": cluster,
            **({"nextToken": next_token} if next_token else {}),
        }
        response = client.list_services(**params)
        services.extend(response["serviceArns"])

        if response.get("nextToken"):
            _list(response["nextToken"])

    _list()
    return services


def filter_services(services: List[str], pattern: str) -> List[str]:
    """Return the list of services matching the given pattern."""
    r = re.compile(pattern)
    return [s for s in services if r.search(s)]


def list_tasks(cluster: str, service: str, client: boto3.client) -> List[str]:
    tasks = []

    def _list(next_token=None):
        params = {
            "cluster": cluster,
            "maxResults": 100,
            **({"serviceName": service} if service else {}),
            **({"nextToken": next_token} if next_token else {}),
        }
        response = client.list_tasks(**params)
        tasks.extend(response["taskArns"])

        if response.get("nextToken"):
            _list(response["nextToken"])

    _list()
    return tasks


def list_running_tasks_in_cluster(
    cluster: str, client: boto3.client, service: str = None
) -> List[str]:
    tasks = []

    def _list(next_token=None):
        params = {
            "cluster": cluster,
            "maxResults": 100,
            "desiredStatus": "RUNNING",
            **({"serviceName": service} if service else {}),
            **({"nextToken": next_token} if next_token else {}),
        }
        response = client.list_tasks(**params)
        tasks.extend(response["taskArns"])

        if response.get("nextToken"):
            _list(response["nextToken"])

    _list()
    return tasks
