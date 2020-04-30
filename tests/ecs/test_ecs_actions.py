# -*- coding: utf-8 -*-
from unittest.mock import ANY, MagicMock, patch
from chaoslib.exceptions import FailedActivity
import pytest
from chaosaws.ecs.actions import (delete_cluster, delete_service,
                                  deregister_container_instance, stop_task,
                                  stop_random_tasks,
                                  update_desired_count)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_no_cluster(aws_client):
    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(service='ecs-service')
    assert 'A cluster name is required' in str(x.value)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_no_count_or_percent(aws_client):
    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster='ecs-cluster')
    assert 'Must specify one of "task_count", "task_percent"' in str(x.value)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_both_count_and_percent(aws_client):
    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster='ecs-cluster', task_count=1, task_percent=1)
    assert 'Must specify one of "task_count", "task_percent"' in str(x.value)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_count_too_high(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 3
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]

    with pytest.raises(FailedActivity) as x:
        stop_random_tasks(cluster=cluster, task_count=task_count, reason=reason)
    assert 'Not enough running tasks in ecs-cluster to satisfy stop count 3 (2)' in str(x.value)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_count_no_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 2
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]
    stop_random_tasks(cluster=cluster, task_count=task_count, reason=reason)

    assert client.stop_task.call_count == 2
    client.stop_task.assert_any_call(cluster=cluster, task="arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da", reason=reason)
    client.stop_task.assert_any_call(cluster=cluster, task="arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk", reason=reason)

@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_percent_no_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_percent = 50
    reason = "unit-test"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]
    stop_random_tasks(cluster=cluster, task_percent=task_percent, reason=reason)

    assert client.stop_task.call_count == 1
    task_calls = ["arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da", "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"]

    ex = None
    for i in task_calls:
        try:
            client.stop_task.assert_called_with(
                cluster=cluster, reason=reason, task=i)
            return True
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)

@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_percent_yes_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_percent = 50
    reason = "unit-test"
    service = "ecs-service"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]
    stop_random_tasks(cluster=cluster, service=service, task_percent=task_percent, reason=reason)

    assert client.stop_task.call_count == 1
    task_calls = ["arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da", "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"]

    ex = None
    for i in task_calls:
        try:
            client.stop_task.assert_called_with(
                cluster=cluster, reason=reason, task=i)
            return True
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)

@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_random_tasks_count_yes_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_count = 2
    reason = "unit-test"
    service = "ecs-service"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]
    stop_random_tasks(cluster=cluster, service=service, task_count=task_count, reason=reason)

    assert client.stop_task.call_count == 2
    client.stop_task.assert_any_call(cluster=cluster, task="arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da", reason=reason)
    client.stop_task.assert_any_call(cluster=cluster, task="arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk", reason=reason)

@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_task(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_id = "16fd2706-8baf-433b-82eb-8c7fada847da"
    reason = "unit test"
    stop_task(cluster=cluster, task_id=task_id, reason=reason)
    client.stop_task.assert_called_with(
        cluster=cluster, task=task_id, reason=reason)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_tasks(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    reason = "unit test"
    client.list_tasks.side_effect = [
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/16fd2706-8baf-433b-82eb-8c7fada847da"], 'nextToken': 'token0'},
        {'taskArns': [
            "arn:aws:ecs:us-east-1:012345678910:task/84th9568-3tth-55g1-35ki-4o9amby245lk"], 'nextToken': None}
    ]
    stop_task(cluster=cluster, service=service, reason=reason)

    args, kwargs = client.stop_task.call_args
    assert kwargs["task"] in ("16fd2706-8baf-433b-82eb-8c7fada847da",
                              "84th9568-3tth-55g1-35ki-4o9amby245lk")


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    svc1 = "my-http-service"

    delete_service(cluster=cluster, service=svc1)
    client.update_service.assert_called_with(
        cluster=cluster, service=svc1, desiredCount=0,
        deploymentConfiguration={
            'maximumPercent': 100,
            'minimumHealthyPercent': 0
        })
    client.delete_service.assert_called_with(cluster=cluster, service=svc1)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_services(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    svc1 = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    svc2 = "arn:aws:ecs:us-east-1:012345678910:service/my-db-service"

    client.list_services.side_effect = [
        {'serviceArns': [svc1], 'nextToken': 'token0'},
        {'serviceArns': [svc2], 'nextToken': None}
    ]

    delete_service(cluster=cluster)
    client.update_service.assert_called_with(
        cluster=cluster, service=ANY, desiredCount=0,
        deploymentConfiguration={
            'maximumPercent': 100,
            'minimumHealthyPercent': 0
        })
    args, kwargs = client.update_service.call_args
    assert kwargs["service"] in ("my-http-service", "my-db-service")

    client.delete_service.assert_called_with(cluster=cluster, service=ANY)
    args, kwargs = client.delete_service.call_args
    assert kwargs["service"] in ("my-http-service", "my-db-service")


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_filtered_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    svc1 = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    svc2 = "arn:aws:ecs:us-east-1:012345678910:service/my-db-service"

    client.list_services.side_effect = [
        {'serviceArns': [svc1], 'nextToken': 'token0'},
        {'serviceArns': [svc2], 'nextToken': None}
    ]

    delete_service(cluster=cluster, service_pattern="my-db")
    client.update_service.assert_called_with(
        cluster=cluster, service="my-db-service", desiredCount=0,
        deploymentConfiguration={
            'maximumPercent': 100,
            'minimumHealthyPercent': 0
        })

    client.delete_service.assert_called_with(
        cluster=cluster, service="my-db-service")


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    delete_cluster(cluster=cluster)
    client.delete_cluster.assert_called_with(cluster=cluster)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_deregister_container_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    inst = "arn:aws:ecs:us-east-1:012345678910:container-instance/myinst"

    deregister_container_instance(cluster=cluster, instance_id=inst)
    client.deregister_container_instance.assert_called_with(
        cluster=cluster, containerInstance=inst, force=False)


def test_no_arguments_error():
    with pytest.raises(TypeError) as x:
        update_desired_count()
    assert 'missing 3 required positional arguments' in str(x.value)


def test_missing_cluster_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(service='my_service', desired_count=1)
    assert "required positional argument: 'cluster'" in str(x.value)


def test_missing_count_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(
            cluster='my_cluster', service='my_service')
    assert "required positional argument: 'desired_count'" in str(x.value)


def test_missing_service_argument_error():
    with pytest.raises(TypeError) as x:
        update_desired_count(
            cluster='my_cluster', desired_count=0)
    assert "required positional argument: 'service'" in str(x.value)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_update_desired_service_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = 'my_cluster'
    service = 'my_service'

    client.describe_clusters = MagicMock(
        return_value={
            'clusters': [{
                'clusterArn': 'arn:aws:ecs:us-east-1::cluster/my_cluster',
                'clusterName': 'my_cluster'
            }]
        }
    )
    client.describe_services = MagicMock(
        return_value={
            'services': [{
                'serviceArn': 'arn:aws:ecs:us-east-1::service/my_service',
                'serviceName': 'my_service'
            }]
        }
    )
    client.update_service = MagicMock(
        return_value={
            'service': {
                'serviceArn': 'arn:aws:ecs:us-east-1::service/my_service',
                'serviceName': 'my_service',
                'desiredCount': 1
            }
        }
    )
    update_desired_count(
        cluster=cluster, service=service, desired_count=1)
    client.describe_clusters.assert_called_with(clusters=[cluster])
    client.update_service.assert_called_with(
        cluster=cluster, service=service, desiredCount=1)
