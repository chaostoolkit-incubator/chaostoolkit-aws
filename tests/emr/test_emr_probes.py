import os
from json import loads
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from moto import mock_aws

from chaosaws.emr.probes import (
    describe_cluster,
    describe_instance_fleet,
    describe_instance_group,
    list_cluster_fleet_instances,
    list_cluster_group_instances,
    list_emr_clusters,
)

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_configs(filename):
    config = os.path.join(data_path, filename)
    with open(config) as fh:
        return loads(fh.read())


def mock_client_error(*args, **kwargs):
    return ClientError(
        operation_name=kwargs["op"],
        error_response={
            "Error": {"Code": kwargs["Code"], "Message": kwargs["Message"]}
        },
    )


@mock_aws
class TestEmrProbesMoto:
    def setup_method(self, *args, **kwargs):
        config = os.path.join(data_path, "cluster_properties.json")
        with open(config) as fh:
            config_data = loads(fh.read())

        client = boto3.client("emr", region_name="us-east-1")
        client.run_job_flow(**config_data)
        c = client.list_clusters()
        clusters = c["Clusters"]
        self.cluster_id = clusters[0]["Id"]
        self.instance_groups = client.list_instance_groups(
            ClusterId=self.cluster_id
        )["InstanceGroups"]

    def test_describe_cluster(self):
        params = {
            "cluster_id": self.cluster_id,
            "configuration": {"aws_region": "us-east-1"},
        }
        response = describe_cluster(**params)
        assert response["Cluster"]["Name"] == "MyTestCluster"

    def test_describe_instance_group(self):
        params = {
            "cluster_id": self.cluster_id,
            "group_id": self.instance_groups[0]["Id"],
            "configuration": {"aws_region": "us-east-1"},
        }
        response = describe_instance_group(**params)
        group = response["InstanceGroups"]
        assert group["Name"] == "MasterGroupNodes"

    def test_list_emr_clusters(self):
        params = {"configuration": {"aws_region": "us-east-1"}}
        response = list_emr_clusters(**params)
        assert response["Clusters"][0]["Id"] == self.cluster_id


class TestEmrProbesMocked:
    def setup_method(self):
        self.cluster_id = "j-BC86D9AZOOHIA"
        self.group_id = "i-123456789ABCD"
        self.fleet_id = "i-987654321ZYWXW"

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_list_cluster_fleet_instances(self, aws_client):
        mocked_response = read_configs("list_instances_1.json")
        client = MagicMock()
        aws_client.return_value = client
        client.list_instances.return_value = mocked_response

        response = list_cluster_fleet_instances(self.cluster_id, self.fleet_id)
        group = response["Instances"]
        assert len(group) == 2

        client.list_instances.assert_called_with(
            ClusterId=self.cluster_id, InstanceFleetId=self.fleet_id
        )

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_list_cluster_group_instances(self, aws_client):
        mocked_response = read_configs("list_instances_2.json")
        client = MagicMock()
        aws_client.return_value = client
        client.list_instances.return_value = mocked_response

        response = list_cluster_group_instances(self.cluster_id, self.group_id)
        group = response["Instances"]
        assert len(group) == 4

        client.list_instances.assert_called_with(
            ClusterId=self.cluster_id, InstanceGroupId=self.group_id
        )

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_list_cluster_group_instances_invalid_group(self, aws_client):
        group_id = "i-INVALID"
        mocked_response = mock_client_error(
            op="DescribeCluster",
            Code="InvalidRequestException",
            Message="Instance group id '%s' is not valid" % group_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.list_instances.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            list_cluster_group_instances(self.cluster_id, group_id)
        assert "Instance group id '%s' is not valid" % group_id in str(e.value)

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_describe_instance_group_invalid_cluster(self, aws_client):
        cluster_id = "i-INVALIDCLUSTER"
        mocked_response = mock_client_error(
            op="DescribeCluster",
            Code="InvalidRequestException",
            Message="Cluster id '%s' is not valid" % cluster_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.list_instance_groups.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            describe_instance_group(cluster_id, "i-IJKLMNOPQ8912")
        assert "Cluster id '%s' is not valid" % cluster_id in str(e.value)

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_describe_instance_fleet(self, aws_client):
        mocked_response = read_configs("list_instance_fleets_1.json")
        client = MagicMock()
        aws_client.return_value = client
        client.list_instance_fleets.return_value = mocked_response

        response = describe_instance_fleet(self.cluster_id, "i-IJKLMNOPQ8912")
        fleet = response["InstanceFleets"]
        assert fleet["Name"] == "TaskFleetNodes"

        client.list_instance_fleets.assert_called_with(
            ClusterId=self.cluster_id
        )

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_describe_cluster_invalid(self, aws_client):
        cluster_id = "i-INVALIDCLUSTER"
        mocked_response = mock_client_error(
            op="DescribeCluster",
            Code="InvalidRequestException",
            Message="Cluster id '%s' is not valid" % cluster_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.describe_cluster.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            describe_cluster(cluster_id=cluster_id)
        assert "Cluster id '%s' is not valid" % cluster_id in str(e.value)

    @patch("chaosaws.emr.probes.aws_client", autospec=True)
    def test_describe_instance_fleet_invalid_cluster(self, aws_client):
        cluster_id = "i-INVALIDCLUSTER"
        mocked_response = mock_client_error(
            op="DescribeCluster",
            Code="InvalidRequestException",
            Message="Cluster id '%s' is not valid" % cluster_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.list_instance_fleets.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            describe_instance_fleet(cluster_id, "i-IJKLMNOPQ8912")
        assert "Cluster id '%s' is not valid" % cluster_id in str(e.value)
