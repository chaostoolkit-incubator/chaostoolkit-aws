# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.ecs.probes import service_is_deploying


@patch('chaosaws.ecs.probes.aws_client', autospec=True)
def test_ecs_service_is_not_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(return_value={
        'services': [{
            'deployments': [
                {"status": "PRIMARY"}
            ]
        }]
    })
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    response = service_is_deploying(cluster, service)
    client.describe_services.assert_called_with(cluster=cluster, services=[service])
    assert response is False


@patch('chaosaws.ecs.probes.aws_client', autospec=True)
def test_ecs_service_is_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(return_value={
        'services': [{
            'deployments': [
                {'status': 'PRIMARY'},
                {'status': 'ACTIVE'}
            ]
        }]
    })
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    response = service_is_deploying(cluster, service)
    client.describe_services.assert_called_with(cluster=cluster, services=[service])
    assert response is True


@patch('chaosaws.ecs.probes.aws_client', autospec=True)
def test_error_checking_ecs_service_is_not_deploying(aws_client):
    client = MagicMock()
    client.describe_services = MagicMock(return_value={
        'services': [],
        'failures': [{
            'reason': 'some_reason',
            'arn': 'some_arn'
        }]
    })
    aws_client.return_value = client
    cluster = "ecs-cluster"
    service = "ecs-service"
    with pytest.raises(FailedActivity) as exceptionInfo:
        service_is_deploying(cluster, service)

    client.describe_services.assert_called_with(cluster=cluster, services=[service])
    assert 'Error retrieving service data from AWS' in str(exceptionInfo.value)