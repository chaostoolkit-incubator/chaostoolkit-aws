from unittest.mock import MagicMock, patch

from chaosaws.eks.actions import create_cluster, delete_cluster


@patch("chaosaws.eks.actions.aws_client", autospec=True)
def test_create_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    arn = "arn:aws:iam::123456:role/EKSrole"
    vpc_config = {"subnetIds": ["sub1"], "securityGroupIds": ["sg1"]}
    create_cluster(name=cluster, role_arn=arn, vpc_config=vpc_config)
    client.create_cluster.assert_called_with(
        name=cluster, roleArn=arn, version=None, resourcesVpcConfig=vpc_config
    )


@patch("chaosaws.eks.actions.aws_client", autospec=True)
def test_delete_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    delete_cluster(name=cluster)
    client.delete_cluster.assert_called_with(name=cluster)
