from unittest.mock import MagicMock, patch
import pytest
from chaosaws.msk.actions import reboot_msk_broker, delete_cluster
from chaoslib.exceptions import FailedActivity


class NotFoundException(Exception):
    def __init__(self, message="Cluster not found"):
        super().__init__(f"{message}")


@patch("chaosaws.msk.actions.aws_client", autospec=True)
def test_reboot_msk_broker_success(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"
    broker_ids = ["1"]
    client.reboot_broker.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    response = reboot_msk_broker(cluster_arn=cluster_arn, broker_ids=broker_ids)

    client.reboot_broker.assert_called_with(
        ClusterArn=cluster_arn, BrokerIds=broker_ids
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


@patch("chaosaws.msk.actions.aws_client", autospec=True)
def test_reboot_msk_broker_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"
    broker_ids = ["1"]

    client.exceptions = MagicMock()
    client.exceptions.NotFoundException = NotFoundException
    client.reboot_broker.side_effect = NotFoundException("Cluster not found")

    expected_error_message = "The specified cluster was not found"

    with pytest.raises(FailedActivity) as exc_info:
        reboot_msk_broker(cluster_arn=cluster_arn, broker_ids=broker_ids)

    assert expected_error_message in str(exc_info.value)


@patch("chaosaws.msk.actions.aws_client", autospec=True)
def test_delete_cluster_success(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"
    client.delete_cluster.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    response = delete_cluster(cluster_arn=cluster_arn)

    client.delete_cluster.assert_called_with(ClusterArn=cluster_arn)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


@patch("chaosaws.msk.actions.aws_client", autospec=True)
def test_delete_cluster_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster_arn = "arn_msk_cluster"

    client.exceptions = MagicMock()
    client.exceptions.NotFoundException = NotFoundException
    client.delete_cluster.side_effect = NotFoundException("Cluster not found")

    expected_error_message = "The specified cluster was not found"

    with pytest.raises(FailedActivity) as exc_info:
        delete_cluster(cluster_arn=cluster_arn)

    assert expected_error_message in str(exc_info.value)
