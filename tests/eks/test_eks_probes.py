from unittest.mock import MagicMock, patch

from chaosaws.eks.probes import describe_cluster, list_clusters


@patch("chaosaws.eks.probes.aws_client", autospec=True)
def test_describe_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    describe_cluster(name=cluster)
    client.describe_cluster.assert_called_with(name=cluster)


@patch("chaosaws.eks.probes.aws_client", autospec=True)
def test_describe_missing_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    x = Exception
    client.exceptions.ResourceNotFoundException = x
    client.describe_cluster.side_effect = x
    response = describe_cluster(name=cluster)
    assert response is None


@patch("chaosaws.eks.probes.aws_client", autospec=True)
def test_list_clusters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    list_clusters()
    client.list_clusters.assert_called_with()
