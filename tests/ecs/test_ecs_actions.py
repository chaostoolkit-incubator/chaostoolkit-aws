# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch, ANY

from chaosaws.ecs.actions import stop_task, delete_service, \
    delete_cluster, deregister_container_instance


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_id = "16fd2706-8baf-433b-82eb-8c7fada847da"
    reason = "unit test"
    response = stop_task(cluster, task_id, reason)
    client.stop_task.assert_called_with(
        cluster=cluster, task=task_id, reason=reason)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    svc1 = "my-http-service"

    response = delete_service(cluster=cluster, service=svc1)
    client.update_service.assert_called_with(
        cluster=cluster, service=svc1, desiredCount=0,
        deploymentConfiguration={
            'maximumPercent': 100,
            'minimumHealthyPercent': 0
        })
    client.delete_service.assert_called_with(cluster=cluster, service=svc1)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_delete_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"

    svc1 = "arn:aws:ecs:us-east-1:012345678910:service/my-http-service"
    svc2 = "arn:aws:ecs:us-east-1:012345678910:service/my-db-service"

    client.list_services.side_effect = [
        {'serviceArns': [svc1], 'nextToken': 'token0'},
        {'serviceArns': [svc2], 'nextToken': None}
    ]

    response = delete_service(cluster=cluster)
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

    response = delete_service(cluster=cluster, service_pattern="my-db")
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

    response = delete_cluster(cluster=cluster)
    client.delete_cluster.assert_called_with(cluster=cluster)


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_deregister_container_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    inst = "arn:aws:ecs:us-east-1:012345678910:container-instance/myinst"

    response = deregister_container_instance(cluster=cluster, instance_id=inst)
    client.deregister_container_instance.assert_called_with(
        cluster=cluster, containerInstance=inst, force=False)
