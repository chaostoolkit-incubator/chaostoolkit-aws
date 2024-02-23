import os
from json import loads
from unittest.mock import ANY, MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.ecs.actions import (
    delete_cluster,
    delete_service,
    deregister_container_instance,
    set_service_deployment_configuration,
    set_service_placement_strategy,
    stop_random_tasks,
    stop_task,
    tag_resource,
    untag_resource,
    update_container_instances_state,
    update_desired_count,
)

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_configs(filename):
    config = os.path.join(data_path, filename)
    with open(config) as fh:
        return loads(fh.read())


def mock_client_error(*args, **kwargs):
    return ClientError(
        operation_name=kwargs["op"],
        error_response={
            "Error": {"Code": kwargs["Code"], "Message": kwargs["Message"]}
        },
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_no_count_or_percent(aws_client):
    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster="ecs-cluster")
    assert 'Must specify one of "task_count", "task_percent"' in str(x.value)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_both_count_and_percent(aws_client):
    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster="ecs-cluster", task_count=1, task_percent=1)
    assert 'Must specify one of "task_count", "task_percent"' in str(x.value)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_count_too_high(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 3
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]

    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster=cluster, task_count=task_count, reason=reason)
    assert (
        "Not enough running tasks in ecs-cluster to satisfy stop count 3 (2)"
        in str(x.value)
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_count_no_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 2
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]
    stop_random_tasks(cluster=cluster, task_count=task_count, reason=reason)

    assert client.stop_task.call_count == 2
    client.stop_task.assert_any_call(
        cluster=cluster,
        task="arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da",  # Noqa
        reason=reason,
    )
    client.stop_task.assert_any_call(
        cluster=cluster,
        task="arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk",  # Noqa
        reason=reason,
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_percent_no_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_percent = 50
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]
    stop_random_tasks(cluster=cluster, task_percent=task_percent, reason=reason)

    assert client.stop_task.call_count == 1
    task_calls = [
        "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da",
        "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk",
    ]

    ex = None
    for i in task_calls:
        try:
            client.stop_task.assert_called_with(
                cluster=cluster, reason=reason, task=i
            )
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_percent_yes_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_percent = 50
    reason = "unit-test"
    service = "ecs-service"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]
    stop_random_tasks(
        cluster=cluster,
        service=service,
        task_percent=task_percent,
        reason=reason,
    )

    assert client.stop_task.call_count == 1
    task_calls = [
        "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da",
        "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk",
    ]

    ex = None
    for i in task_calls:
        try:
            client.stop_task.assert_called_with(
                cluster=cluster, reason=reason, task=i
            )
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_random_tasks_count_yes_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 2
    reason = "unit-test"
    service = "ecs-service"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]
    stop_random_tasks(
        cluster=cluster, service=service, task_count=task_count, reason=reason
    )

    assert client.stop_task.call_count == 2
    client.stop_task.assert_any_call(
        cluster=cluster,
        task="arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da",  # Noqa
        reason=reason,
    )
    client.stop_task.assert_any_call(
        cluster=cluster,
        task="arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk",  # Noqa
        reason=reason,
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_task(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_id = "16fd2706-8baf-433b-82eb-8c7fada847da"
    reason = "unit test"
    stop_task(cluster=cluster, task_id=task_id, reason=reason)
    client.stop_task.assert_called_with(
        cluster=cluster, task=task_id, reason=reason
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_stop_tasks(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    reason = "unit test"
    client.list_tasks.side_effect = [
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"  # Noqa
            ],
            "nextToken": "token0",
        },
        {
            "taskArns": [
                "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"  # Noqa
            ],
            "nextToken": None,
        },
    ]
    stop_task(cluster=cluster, service=service, reason=reason)

    args, kwargs = client.stop_task.call_args
    assert kwargs["task"] in (
        "16fd2706-8baf-433b-82eb-8c7fada847da",
        "84th9568-3tth-55g1-35ki-4o9amby245lk",
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_delete_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    svc1 = "my-http-service"

    delete_service(cluster=cluster, service=svc1)
    client.update_service.assert_called_with(
        cluster=cluster,
        service=svc1,
        desiredCount=0,
        deploymentConfiguration={
            "maximumPercent": 100,
            "minimumHealthyPercent": 0,
        },
    )
    client.delete_service.assert_called_with(cluster=cluster, service=svc1)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_delete_services(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    svc1 = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    svc2 = "arn:aws:ecs:us-east-1:012345678910:service/my-db-service"

    client.list_services.side_effect = [
        {"serviceArns": [svc1], "nextToken": "token0"},
        {"serviceArns": [svc2], "nextToken": None},
    ]

    delete_service(cluster=cluster)
    client.update_service.assert_called_with(
        cluster=cluster,
        service=ANY,
        desiredCount=0,
        deploymentConfiguration={
            "maximumPercent": 100,
            "minimumHealthyPercent": 0,
        },
    )
    args, kwargs = client.update_service.call_args
    assert kwargs["service"] in ("my-http-service", "my-db-service")

    client.delete_service.assert_called_with(cluster=cluster, service=ANY)
    args, kwargs = client.delete_service.call_args
    assert kwargs["service"] in ("my-http-service", "my-db-service")


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_delete_filtered_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    svc1 = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    svc2 = "arn:aws:ecs:us-east-1:012345678910:service/my-db-service"

    client.list_services.side_effect = [
        {"serviceArns": [svc1], "nextToken": "token0"},
        {"serviceArns": [svc2], "nextToken": None},
    ]

    delete_service(cluster=cluster, service_pattern="my-db")
    client.update_service.assert_called_with(
        cluster=cluster,
        service="my-db-service",
        desiredCount=0,
        deploymentConfiguration={
            "maximumPercent": 100,
            "minimumHealthyPercent": 0,
        },
    )

    client.delete_service.assert_called_with(
        cluster=cluster, service="my-db-service"
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_delete_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    delete_cluster(cluster=cluster)
    client.delete_cluster.assert_called_with(cluster=cluster)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_deregister_container_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    inst = "arn:aws:ecs:us-east-1:012345678910:container-instance/myinst"

    deregister_container_instance(cluster=cluster, instance_id=inst)
    client.deregister_container_instance.assert_called_with(
        cluster=cluster, containerInstance=inst, force=False
    )


def test_no_arguments_error():
    with pytest.raises(TypeError) as x:
        update_desired_count()
    assert "missing 3 required positional arguments" in str(x.value)


def test_missing_cluster_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(service="my_service", desired_count=1)
    assert "required positional argument: 'cluster'" in str(x.value)


def test_missing_count_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(cluster="my_cluster", service="my_service")
    assert "required positional argument: 'desired_count'" in str(x.value)


def test_missing_service_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(cluster="my_cluster", desired_count=0)
    assert "required positional argument: 'service'" in str(x.value)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_update_desired_service_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "my_cluster"
    service = "my_service"

    client.describe_clusters = MagicMock(
        return_value={
            "clusters": [
                {
                    "clusterArn": "arn:aws:ecs:us-east-1::cluster/my_cluster",
                    "clusterName": "my_cluster",
                }
            ]
        }
    )
    client.describe_services = MagicMock(
        return_value={
            "services": [
                {
                    "serviceArn": "arn:aws:ecs:us-east-1::service/my_service",
                    "serviceName": "my_service",
                }
            ]
        }
    )
    client.update_service = MagicMock(
        return_value={
            "service": {
                "serviceArn": "arn:aws:ecs:us-east-1::service/my_service",
                "serviceName": "my_service",
                "desiredCount": 1,
            }
        }
    )
    update_desired_count(cluster=cluster, service=service, desired_count=1)
    client.describe_clusters.assert_called_with(clusters=[cluster])
    client.update_service.assert_called_with(
        cluster=cluster, service=service, desiredCount=1
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_placement_strategy(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = read_configs(
        "describe_clusters_1.json"
    )
    client.describe_services.return_value = read_configs(
        "describe_services_1.json"
    )
    client.update_service.return_value = read_configs("update_service_1.json")

    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyTestEcsService",
        "placement_type": "random",
    }
    set_service_placement_strategy(**params)
    client.update_service.assert_called_with(
        cluster="MyTestEcsCluster",
        service="MyTestEcsService",
        placementStrategy=[{"type": "random"}],
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_placement_strategy_invalid_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = {"clusters": []}

    params = {
        "cluster": "MyInvalidCluster",
        "service": "MyTestEcsService",
        "placement_type": "random",
    }
    with pytest.raises(FailedActivity) as e:
        set_service_placement_strategy(**params)
    assert "unable to locate cluster: MyInvalidCluster" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_placement_strategy_invalid_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = read_configs(
        "describe_clusters_1.json"
    )
    client.describe_services.return_value = {"services": []}

    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyInvalidService",
        "placement_type": "random",
    }
    with pytest.raises(FailedActivity) as e:
        set_service_placement_strategy(**params)
    assert "unable to locate service: MyInvalidService" in str(e)


def test_set_service_placement_strategy_invalid_param_1():
    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyTestEcsService",
        "placement_type": "spread",
    }
    with pytest.raises(FailedActivity) as e:
        set_service_placement_strategy(**params)
    assert '"placement_field" is required when using' in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_placement_strategy_invalid_param_2(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = read_configs(
        "describe_clusters_1.json"
    )
    client.describe_services.return_value = read_configs(
        "describe_services_1.json"
    )

    params = {
        "op": "UpdateService",
        "Code": "InvalidParameterException",
        "Message": "An error occurred (InvalidParameterException)",
    }
    client.update_service.side_effect = mock_client_error(**params)

    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyTestEcsService",
        "placement_type": "xrandom",
    }
    with pytest.raises(FailedActivity) as e:
        set_service_placement_strategy(**params)
    assert "An error occurred (InvalidParameterException)" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_deployment_configuration(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = read_configs(
        "describe_clusters_1.json"
    )
    client.describe_services.return_value = read_configs(
        "describe_services_1.json"
    )
    client.update_service.return_value = read_configs("update_service_2.json")

    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyTestEcsService",
        "maximum_percent": 300,
        "minimum_healthy_percent": 50,
    }
    set_service_deployment_configuration(**params)
    client.update_service.assert_called_with(
        cluster="MyTestEcsCluster",
        service="MyTestEcsService",
        deploymentConfiguration={
            "maximumPercent": 300,
            "minimumHealthyPercent": 50,
        },
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_deployment_configuration_invalid_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = {"clusters": []}

    params = {
        "cluster": "MyInvalidCluster",
        "service": "MyTestEcsService",
        "maximum_percent": 100,
    }
    with pytest.raises(FailedActivity) as e:
        set_service_deployment_configuration(**params)
    assert "unable to locate cluster: MyInvalidCluster" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_set_service_deployment_configuration_invalid_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = read_configs(
        "describe_clusters_1.json"
    )
    client.describe_services.return_value = {"services": []}

    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyInvalidService",
        "maximum_percent": 100,
    }
    with pytest.raises(FailedActivity) as e:
        set_service_deployment_configuration(**params)
    assert "unable to locate service: MyInvalidService" in str(e)


def test_set_service_deployment_configuration_invalid_minimum():
    params = {
        "cluster": "MyTestEcsCluster",
        "service": "MyTestEcsService",
        "maximum_percent": 50,
        "minimum_healthy_percent": 100,
    }
    with pytest.raises(FailedActivity) as e:
        set_service_deployment_configuration(**params)
    assert "minimum_healthy_percent cannot be larger" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_tag_resource(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.tag_resource.return_value = {}

    arn = "arn:aws:ecs:us-east-1:012345678910:cluster/MyTestEcsCluster"
    tags = [{"key": "Name", "value": "MyTestEcsCluster"}]
    tag_resource(tags, arn)
    client.tag_resource.assert_called_with(resourceArn=arn, tags=tags)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_tag_resource_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.tag_resource.side_effect = mock_client_error(
        op="TagResource",
        Code="ClusterNotFoundException",
        Message="An error occurred (ClusterNotFoundException) when calling the "
        "TagResource operation: Cluster not found.",
    )

    arn = "arn:aws:ecs:us-east-1:012345678910:service/MyTestEcsCluster1/"
    tags = [{"key": "Name", "value": "MyTestEcsCluster"}]
    with pytest.raises(FailedActivity) as e:
        tag_resource(tags, arn)
    assert "Cluster not found" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_untag_resource(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.untag_resource.return_value = {}

    arn = (
        "arn:aws:ecs:us-east-1:012345678910:service/MyTestEcsCluster/"
        "MyTestEcsService"
    )
    tag_keys = ["Purpose"]
    untag_resource(tag_keys, arn)
    client.untag_resource.assert_called_with(resourceArn=arn, tagKeys=tag_keys)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_untag_resource_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.untag_resource.side_effect = mock_client_error(
        op="UntagResource",
        Code="ClusterNotFoundException",
        Message="An error occurred (ClusterNotFoundException) when calling the "
        "UntagResource operation: Cluster not found.",
    )

    arn = (
        "arn:aws:ecs:us-east-1:012345678910:service/MyTestEcsCluster1/"
        "MyTestEcsService"
    )
    tag_keys = ["Purpose"]
    with pytest.raises(FailedActivity) as e:
        untag_resource(tag_keys, arn)
    assert "Cluster not found" in str(e)


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_update_container_instance_state(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.update_container_instance_state.return_value = read_configs(
        "update_container_instance_state_1.json"
    )

    arns = [
        "arn:aws:ecs:us-east-1:123456789012:container-instance/"
        "a1b2c3d4-5678-90ab-cdef-11111"
    ]

    update_container_instances_state(
        cluster="MyTestEcsCluster", container_instances=arns, status="DRAINING"
    )

    client.update_container_instance_state.assert_called_with(
        cluster="MyTestEcsCluster", containerInstances=arns, status="DRAINING"
    )


@patch("chaosaws.ecs.actions.aws_client", autospec=True)
def test_update_container_instance_state_invalid_status(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.update_container_instance_state.side_effect = mock_client_error(
        op="UpdateContainerInstanceState",
        Code="InvalidParameterException",
        Message="Container instances status should be one of [ACTIVE,DRAINING]",
    )
    with pytest.raises(FailedActivity) as e:
        update_container_instances_state(
            cluster="MyTestEcsCluster",
            container_instances=[
                "arn:aws:ecs:us-east-1:x:container-instance/z"
            ],
            status="INVALID",
        )
    assert "ACTIVE,DRAINING" in str(e)
