from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.ecs.probes import (
    are_all_desired_tasks_running,
    describe_cluster,
    describe_service,
    describe_tasks,
    service_is_deploying,
)


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_ecs_service_is_not_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(
        return_value={"services": [{"deployments": [{"status": "PRIMARY"}]}]}
    )
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    response = service_is_deploying(cluster, service)
    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert response is False


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_ecs_service_is_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(
        return_value={
            "services": [
                {"deployments": [{"status": "PRIMARY"}, {"status": "ACTIVE"}]}
            ]
        }
    )
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    response = service_is_deploying(cluster, service)
    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert response is True


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_error_checking_ecs_service_is_not_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(
        return_value={
            "services": [],
            "failures": [{"reason": "some_reason", "arn": "some_arn"}],
        }
    )
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    with pytest.raises(FailedActivity) as exceptionInfo:
        service_is_deploying(cluster, service)

    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert "Error retrieving service data from AWS" in str(exceptionInfo.value)


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_are_all_tasks_running_true(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(
        return_value={
            "services": [
                {
                    "serviceName": "MyGenericService",
                    "desiredCount": 3,
                    "runningCount": 3,
                }
            ]
        }
    )
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "MyGenericService"
    response = are_all_desired_tasks_running(cluster, service)
    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert response


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_are_all_tasks_running_false(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(
        return_value={
            "services": [
                {
                    "serviceName": "MyGenericService",
                    "desiredCount": 3,
                    "runningCount": 2,
                }
            ]
        }
    )
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "MyGenericService"
    response = are_all_desired_tasks_running(cluster, service)
    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert not response


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_are_all_tasks_running_exception(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(return_value={"services": []})
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "MyGenericService"
    with pytest.raises(FailedActivity) as e:
        are_all_desired_tasks_running(cluster, service)
    client.describe_services.assert_called_with(
        cluster=cluster, services=[service]
    )
    assert "Error retrieving service data from AWS" in str(e.value)


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_describe_clusters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_clusters.return_value = {
        "clusters": [
            {
                "clusterArn": "arn:aws:ecs:region:012345678910:cluster/MyCluster",
                "clusterName": "MyCluster",
                "status": "ACTIVE",
            }
        ]
    }
    response = describe_cluster(cluster="MyCluster")
    client.describe_clusters.assert_called_with(clusters=["MyCluster"])
    assert response["clusters"][0]["clusterName"] == "MyCluster"


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_describe_service(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_services.return_value = {
        "services": [
            {
                "clusterArn": "arn:aws:ecs:region:012345678910:cluster/MyCluster",
                "serviceArn": "arn:aws:ecs:region:012345678910:service/MyService",
                "serviceName": "MyService",
                "status": "ACTIVE",
            }
        ]
    }
    response = describe_service(cluster="MyCluster", service="MyService")
    client.describe_services.assert_called_with(
        cluster="MyCluster", services=["MyService"]
    )
    assert response["services"][0]["serviceName"] == "MyService"


@patch("chaosaws.ecs.probes.aws_client", autospec=True)
def test_describe_tasks(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_paginator.return_value.paginate.return_value = [
        {
            "taskArns": [
                "arn:aws:ecs:region:012345678910:task/MyCluster/123456789"
            ]
        }
    ]
    client.describe_tasks.return_value = {
        "tasks": [
            {
                "clusterArn": "arn:aws:ecs:region:012345678910:cluster/"
                "MyCluster",
                "taskArn": "arn:aws:ecs:region:012345678910:task/MyCluster/"
                "123456789",
                "version": 22,
            }
        ]
    }
    response = describe_tasks(cluster="MyCluster")
    client.get_paginator.return_value.paginate.assert_called_with(
        cluster="MyCluster"
    )
    client.describe_tasks.assert_called_with(
        cluster="MyCluster",
        tasks=["arn:aws:ecs:region:012345678910:task/MyCluster/123456789"],
    )
    assert response["tasks"][0]["version"] == 22
