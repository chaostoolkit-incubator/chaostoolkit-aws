from unittest.mock import MagicMock, patch
import pytest
from chaosaws.msk.probes import describe_msk_cluster, get_bootstrap_servers
from chaoslib.exceptions import FailedActivity


class NotFoundException(Exception):
    def __init__(self, message="Cluster not found"):
        super().__init__(f"{message}")


@patch("chaosaws.msk.probes.aws_client", autospec=True)
def test_describe_msk_cluster_success(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"
    expected_response = {"ClusterInfo": {"ClusterArn": cluster_arn}}

    client.describe_cluster.return_value = expected_response

    response = describe_msk_cluster(cluster_arn=cluster_arn)

    client.describe_cluster.assert_called_with(ClusterArn=cluster_arn)
    assert response == expected_response


@patch("chaosaws.msk.probes.aws_client", autospec=True)
def test_describe_msk_cluster_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"

    client.exceptions = MagicMock()
    client.exceptions.NotFoundException = NotFoundException
    client.describe_cluster.side_effect = NotFoundException("Cluster not found")

    expected_error_message = "The specified cluster was not found"

    with pytest.raises(FailedActivity) as exc_info:
        describe_msk_cluster(cluster_arn=cluster_arn)

    assert expected_error_message in str(exc_info.value)


@patch("chaosaws.msk.probes.aws_client", autospec=True)
def test_get_bootstrap_servers_success(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"
    bootstrap_servers = "broker1,broker2,broker3"
    expected_response = {"BootstrapBrokerString": bootstrap_servers}

    client.get_bootstrap_brokers.return_value = expected_response

    response = get_bootstrap_servers(cluster_arn=cluster_arn)

    client.get_bootstrap_brokers.assert_called_with(ClusterArn=cluster_arn)
    assert response == bootstrap_servers.split(",")


@patch("chaosaws.msk.probes.aws_client", autospec=True)
def test_get_bootstrap_server_cluster_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"

    client.exceptions = MagicMock()
    client.exceptions.NotFoundException = NotFoundException
    client.get_bootstrap_brokers.side_effect = NotFoundException(
        "Cluster not found"
    )

    expected_error_message = "The specified cluster was not found"

    with pytest.raises(FailedActivity) as exc_info:
        get_bootstrap_servers(cluster_arn=cluster_arn)

    assert expected_error_message in str(exc_info.value)
