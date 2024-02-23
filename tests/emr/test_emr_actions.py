import os
from json import loads
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from moto import mock_aws

from chaosaws.emr.actions import (
    modify_cluster,
    modify_instance_fleet,
    modify_instance_groups_instance_count,
    modify_instance_groups_shrink_policy,
)
from chaosaws.emr.probes import describe_instance_group

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
class TestEmrActionsMoto:
    def setup_method(self, *args, **kwargs):
        config = os.path.join(data_path, "cluster_properties.json")
        with open(config) as fh:
            config_data = loads(fh.read())

        client = boto3.client("emr", region_name="us-east-1")
        client.run_job_flow(**config_data)
        clusters = client.list_clusters()["Clusters"]
        self.cluster_id = clusters[0]["Id"]
        self.instance_groups = client.list_instance_groups(
            ClusterId=self.cluster_id
        )["InstanceGroups"]
        self.group_id0 = self.instance_groups[0]["Id"]

    def test_modify_instance_groups_instance_count(self):
        # assert original cluster RequestedInstanceCount
        params = {
            "cluster_id": self.cluster_id,
            "group_id": self.group_id0,
            "configuration": {"aws_region": "us-east-1"},
        }
        response = describe_instance_group(**params)
        group = response["InstanceGroups"]
        assert group["Name"] == "MasterGroupNodes"
        assert group["RequestedInstanceCount"] == 3

        # modify RequestedInstanceCount and assert changed value
        params = {
            "cluster_id": self.cluster_id,
            "group_id": self.instance_groups[0]["Id"],
            "instance_count": 2,
            "configuration": {"aws_region": "us-east-1"},
        }
        response = modify_instance_groups_instance_count(**params)
        group = response["InstanceGroups"]
        assert group["Name"] == "MasterGroupNodes"
        assert group["RequestedInstanceCount"] == 2


class TestEmrActionsMock:
    def setup_method(self):
        self.fleet_id = "i-IJKLMNOPQ8912"
        self.cluster_id = "j-BC86D9AZOOHIA"
        self.group_id = "i-123456789EFGH"

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_instance_groups_invalid_cluster(self, aws_client):
        cluster_id = "j-123456789AAZ"
        mocked_response = mock_client_error(
            op="ModifyInstanceGroups",
            Code="ValidationException",
            Message="Cluster id '%s' is not valid." % cluster_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.modify_instance_groups.side_effect = mocked_response
        params = {
            "cluster_id": cluster_id,
            "group_id": self.group_id,
            "instance_count": 2,
        }
        with pytest.raises(FailedActivity) as e:
            modify_instance_groups_instance_count(**params)
        assert "Cluster id '%s' is not valid" % cluster_id in str(e.value)

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_cluster(self, aws_client):
        mocked_response = {"StepConcurrencyLevel": 25}
        client = MagicMock()
        aws_client.return_value = client
        client.modify_cluster.return_value = mocked_response

        modify_cluster(cluster_id=self.cluster_id, concurrency=25)
        client.modify_cluster.assert_called_with(
            ClusterId=self.cluster_id, StepConcurrencyLevel=25
        )

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_cluster_invalid_cluster(self, aws_client):
        cluster_id = "j-123456789AAZ"
        mocked_response = mock_client_error(
            op="ModifyCluster",
            Code="ValidationException",
            Message="Cluster id '%s' is not valid." % cluster_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.modify_cluster.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            modify_cluster(cluster_id=self.cluster_id, concurrency=10)
        assert "Cluster id '%s' is not valid" % cluster_id in str(e.value)

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_instance_groups_shrink_policy(self, aws_client):
        mocked_response = read_configs("list_instance_groups_1.json")
        client = MagicMock()
        aws_client.return_value = client
        client.list_instance_groups.return_value = mocked_response
        client.modify_instance_groups.return_value = None

        # modify RequestedInstanceCount and assert changed value
        params = {
            "cluster_id": self.cluster_id,
            "group_id": self.group_id,
            "decommission_timeout": 180,
            "terminate_instances": ["i-123456789123"],
            "protect_instances": ["i-111111111111"],
            "termination_timeout": 500,
        }
        modify_instance_groups_shrink_policy(**params)
        client.modify_instance_groups.assert_called_with(
            ClusterId=self.cluster_id,
            InstanceGroups=[
                {
                    "InstanceGroupId": self.group_id,
                    "ShrinkPolicy": {
                        "DecommissionTimeout": 180,
                        "InstanceResizePolicy": {
                            "InstancesToTerminate": ["i-123456789123"],
                            "InstancesToProtect": ["i-111111111111"],
                            "InstanceTerminationTimeout": 500,
                        },
                    },
                }
            ],
        )

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_instance_groups_shrink_policy_bad_group(self, aws_client):
        group_id = "i-INVALIDGROUP"
        mocked_response = mock_client_error(
            op="ModifyInstanceGroups",
            Code="ValidationException",
            Message="Group id '%s' is not valid." % group_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.modify_instance_groups.side_effect = mocked_response

        params = {
            "cluster_id": self.cluster_id,
            "group_id": group_id,
            "decommission_timeout": 180,
            "terminate_instances": ["i-123456789123"],
            "protect_instances": ["i-111111111111"],
            "termination_timeout": 500,
        }
        with pytest.raises(FailedActivity) as e:
            modify_instance_groups_shrink_policy(**params)

        assert "Group id '%s' is not valid" % group_id in str(e.value)

    def test_modify_instance_groups_shrink_policy_bad_args_1(self):
        params = {"cluster_id": self.cluster_id, "group_id": self.group_id}
        with pytest.raises(FailedActivity) as e:
            modify_instance_groups_shrink_policy(**params)
        assert "Must provide at least one of" in str(e)

    def test_modify_instance_groups_shrink_policy_bad_args_2(self):
        params = {
            "cluster_id": self.cluster_id,
            "group_id": self.group_id,
            "decommission_timeout": 180,
            "termination_timeout": 500,
        }
        with pytest.raises(FailedActivity) as e:
            modify_instance_groups_shrink_policy(**params)
        assert 'Must provide "terminate_instances" when' in str(e)

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_instance_fleet(self, aws_client):
        mocked_response = read_configs("list_instance_fleets_1.json")
        client = MagicMock()
        aws_client.return_value = client
        client.list_instance_fleets.return_value = mocked_response
        client.modify_instance_fleet.return_value = None

        modify_instance_fleet(
            cluster_id=self.cluster_id,
            fleet_id=self.fleet_id,
            on_demand_capacity=3,
            spot_capacity=2,
        )
        client.modify_instance_fleet.assert_called_with(
            ClusterId=self.cluster_id,
            InstanceFleet={
                "InstanceFleetId": self.fleet_id,
                "TargetOnDemandCapacity": 3,
                "TargetSpotCapacity": 2,
            },
        )

    def test_modify_instance_fleet_no_args(self):
        with pytest.raises(FailedActivity) as e:
            modify_instance_fleet(
                cluster_id=self.cluster_id, fleet_id=self.fleet_id
            )
        assert "Must provide at least one of" in str(e)

    @patch("chaosaws.emr.actions.aws_client", autospec=True)
    def test_modify_instance_fleet_invalid_fleet(self, aws_client):
        fleet_id = "i-JKEIDBGHSJ34"
        mocked_response = mock_client_error(
            op="ModifyInstanceFleet",
            Code="ValidationException",
            Message="Fleet id '%s' is not valid." % fleet_id,
        )
        client = MagicMock()
        aws_client.return_value = client
        client.modify_instance_fleet.side_effect = mocked_response

        with pytest.raises(FailedActivity) as e:
            modify_instance_fleet(
                cluster_id=self.cluster_id,
                fleet_id=fleet_id,
                on_demand_capacity=3,
                spot_capacity=2,
            )
        assert "Fleet id '%s' is not valid" % fleet_id in str(e.value)
