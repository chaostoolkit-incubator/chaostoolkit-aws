# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, Mock, patch

from chaosaws.eks.actions import create_cluster, delete_cluster, \
    terminate_random_nodes


@patch('chaosaws.eks.actions.aws_client', autospec=True)
def test_create_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    arn = "arn:aws:iam::123456:role/EKSrole"
    vpc_config = {
        "subnetIds": ["sub1"],
        "securityGroupIds": ["sg1"]
    }
    create_cluster(
        name=cluster, role_arn=arn, vpc_config=vpc_config)
    client.create_cluster.assert_called_with(
        name=cluster, roleArn=arn, version=None, resourcesVpcConfig=vpc_config)


@patch('chaosaws.eks.actions.aws_client', autospec=True)
def test_delete_cluster(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "eks-cluster"
    delete_cluster(name=cluster)
    client.delete_cluster.assert_called_with(name=cluster)


@patch("chaosaws.eks.actions.aws_client", autospec=True)
@patch("chaosaws.eks.actions.terminate_instance", autospec=True)
def test_terminate_random_nodes_should_terminate_correct_count(
        terminate_instance,
        aws_client):
    terminate_calls = 0

    def terminate_side_effect(*args):
        nonlocal terminate_calls
        terminate_calls = terminate_calls + 1
        return [Mock()]

    ec2_client = MagicMock()
    ec2_client.describe_instances.side_effect = [
            {"Reservations": [
                {"Instances": [{"InstanceId": "foo"}]}
            ]},
            {"Reservations": [
                {"Instances": [{"State": {"Name": "terminated"}}]}
            ]}
        ]
    aws_client.return_value = ec2_client
    terminate_instance.side_effect = terminate_side_effect
    terminate_random_nodes("awdasd", "eu_west_00", 1, 30)

    assert terminate_calls == 1
    terminate_instance.assert_called_with("foo")
