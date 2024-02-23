from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.ec2.probes import (
    count_instances,
    count_min_instances,
    describe_instances,
    instance_state,
)


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_describe_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{"Name": "availability-zone", "Values": ["us-west-1"]}]
    describe_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_count_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{"Name": "availability-zone", "Values": ["us-west-1"]}]
    count_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_instance_state_no_state(aws_client):
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    with pytest.raises(TypeError) as x:
        instance_state(instance_ids=instance_ids)
    assert "missing 1 required positional argument: 'state'" in str(x.value)


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_instance_state_no_query(aws_client):
    with pytest.raises(FailedActivity) as x:
        instance_state(state="running")
    assert (
        'Probe "instance_state" missing required parameter '
        '"instance_ids" or "filters"' in str(x.value)
    )


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_instance_state(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "State": {"Name": "running"},
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "State": {"Name": "running"},
                    },
                ]
            }
        ]
    }
    results = instance_state(state="running", instance_ids=instance_ids)
    client.describe_instances.assert_called_with(InstanceIds=instance_ids)
    assert results


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_instance_state_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{"Name": "instance-type", "Values": ["t2.large"]}]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-987654321fedcba",
                        "State": {"Name": "running"},
                        "InstanceType": "t2.large",
                    }
                ]
            }
        ]
    }
    results = instance_state(state="running", filters=filters)
    client.describe_instances.assert_called_with(Filters=filters)
    assert results


@patch("chaosaws.ec2.probes.aws_client", autospec=True)
def test_count_min_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{"Name": "availability-zone", "Values": ["us-west-1"]}]
    count_min_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)
