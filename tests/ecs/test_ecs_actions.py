# -*- coding: utf-8 -*-
from unittest.mock import ANY, MagicMock, patch

from chaosaws.ecs.actions import (delete_cluster, delete_service,
                                  deregister_container_instance, stop_task)


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
