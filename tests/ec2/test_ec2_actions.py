from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.ec2.actions import (
    attach_volume,
    authorize_security_group_ingress,
    detach_random_volume,
    remove_tags_from_instances,
    restart_instances,
    revoke_security_group_ingress,
    set_tags_on_instances,
    start_instances,
    stop_instance,
    stop_instances,
    terminate_instance,
    terminate_instances,
)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }
    stop_instance(inst_id)
    client.stop_instances.assert_called_with(InstanceIds=[inst_id], Force=False)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_spot_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = "sir-abcdef01"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": inst_id,
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_request_id,
                    }
                ]
            }
        ]
    }
    stop_instance(inst_id)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id]
    )
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }
    stop_instance(inst_id, force=True)
    client.stop_instances.assert_called_with(InstanceIds=[inst_id], Force=True)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_spot_instance_can_be_forced(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = "sir-abcdef01"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": inst_id,
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_request_id,
                    }
                ]
            }
        ]
    }
    stop_instance(inst_id, force=True)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id]
    )
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_ids = ["i-1234567890abcdef0", "i-987654321fedcba"]
    spot_request_id = "sir-abcdef01"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_ids[0], "InstanceLifecycle": "normal"},
                    {
                        "InstanceId": inst_ids[1],
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_request_id,
                    },
                ]
            }
        ]
    }
    stop_instances(inst_ids)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_ids[0]], Force=False
    )
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id]
    )
    client.terminate_instances.assert_called_with(InstanceIds=[inst_ids[1]])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_random_instance_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    stop_instance(az="us-west-1")
    client.stop_instances.assert_called_with(InstanceIds=[inst_id], Force=False)


def test_stop_random_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instance()
    assert (
        "stop an EC2 instance, you must specify either the instance id,"
        " an AZ to pick a random instance from, or a set of filters."
        in str(x.value)
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_all_instances_in_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    inst_2_id = "i-123456789abcdef"
    spot_request_id = "sir-abcdef01"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_1_id, "InstanceLifecycle": "normal"},
                    {
                        "InstanceId": inst_2_id,
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_request_id,
                    },
                ]
            }
        ]
    }

    stop_instances(az="us-west-1")
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False
    )
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id]
    )
    client.terminate_instances.assert_called_with(InstanceIds=[inst_2_id])


def test_stop_all_instances_needs_instance_id_or_az():
    with pytest.raises(FailedActivity) as x:
        stop_instances()
    assert (
        "To stop EC2 instances, you must specify either the instance ids,"
        " an AZ to pick random instances from, or a set of filters."
        in str(x.value)
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_all_instances_may_not_have_any_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }

    with pytest.raises(FailedActivity) as x:
        stop_instances(az="us-west-1")
    assert "No instances in availability zone: us-west-1" in str(x.value)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_instance_by_specific_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_1_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    filters = [
        {
            "Name": "instance-state-name",
            "Values": ["running"],
        },
        {
            "Name": "tag-key",
            "Values": ["eksctl.cluster.k8s.io/v1alpha1/cluster-name"],
        },
        {"Name": "tag-value", "Values": ["chaos-cluster"]},
        {"Name": "tag-key", "Values": ["kubernetes.io/cluster/chaos-cluster"]},
        {"Name": "tag-value", "Values": ["owned"]},
    ]

    stop_instances(filters=filters, az="us-west-2")

    called_filters = deepcopy(filters)
    called_filters.append(
        {"Name": "availability-zone", "Values": ["us-west-2"]}
    )
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.stop_instances.assert_called_with(
        InstanceIds=[inst_1_id], Force=False
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_instance_with_no_lifecycle(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": [{"InstanceId": inst_id}]}]
    }
    stop_instance(inst_id)
    client.stop_instances.assert_called_with(InstanceIds=[inst_id], Force=False)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_stop_normal_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }
    stop_instance(inst_id)
    client.stop_instances.assert_called_with(InstanceIds=[inst_id], Force=False)


###
# Terminate Instance
###
def test_terminate_instance_no_values():
    with pytest.raises(FailedActivity) as x:
        terminate_instance()
    assert (
        "To terminate an EC2, you must specify the instance-id, "
        "an Availability Zone, or provide a set of filters" in str(x.value)
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_instance_az_no_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    az = "us-west-2"
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }
    filters = [{"Name": "availability-zone", "Values": ["us-west-2"]}]
    with pytest.raises(FailedActivity) as x:
        terminate_instance(az=az)
    assert "No instances found matching filters: %s" % filters in str(x.value)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_normal_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }
    terminate_instance(inst_id)
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_spot_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    spot_request_id = "sir-abcdef01"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": inst_id,
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_request_id,
                    }
                ]
            }
        ]
    }
    terminate_instance(inst_id)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=[spot_request_id]
    )
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_random_az_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    terminate_instance(az="us-west-1")
    client.terminate_instances.assert_called_with(InstanceIds=[inst_id])


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_instance_by_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_1_id = "i-987654321fedcba"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_1_id, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    filters = [
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag-value", "Values": ["chaos-cluster"]},
        {"Name": "tag-key", "Values": ["kubernetes.io/cluster/chaos-cluster"]},
        {"Name": "tag-value", "Values": ["owned"]},
        {
            "Name": "tag-key",
            "Values": ["eksctl.cluster.k8s.io/v1alpha1/cluster-name"],
        },
    ]
    terminate_instance(filters=filters, az="us-west-2")

    called_filters = deepcopy(filters)
    called_filters.append(
        {"Name": "availability-zone", "Values": ["us-west-2"]}
    )
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.terminate_instances.assert_called_with(InstanceIds=[inst_1_id])


###
# Terminate Instances
###
def test_terminate_instances_no_values():
    with pytest.raises(FailedActivity) as x:
        terminate_instances()
    assert (
        "To terminate instances, you must specify the instance-id, an "
        "Availability Zone, or provide a set of filters" in str(x.value)
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_instances_az_no_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    az = "us-west-2"
    filters = [{"Name": "availability-zone", "Values": ["us-west-2"]}]
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }

    with pytest.raises(FailedActivity) as x:
        terminate_instances(az=az)
    assert "No instances found matching filters: %s" % filters in str(x.value)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_normal_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }
    terminate_instances(instance_ids)
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_spot_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    spot_ids = ["sir-abcdef01", "sir-fedcba10"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_ids[0],
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "spot",
                        "SpotInstanceRequestId": spot_ids[1],
                    },
                ]
            }
        ]
    }
    terminate_instances(instance_ids)
    client.cancel_spot_instance_requests.assert_called_with(
        SpotInstanceRequestIds=spot_ids
    )
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_random_az_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }

    terminate_instances(az="us-west-1")
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_terminate_instances_by_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }

    filters = [
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag-value", "Values": ["chaos-cluster"]},
        {"Name": "tag-key", "Values": ["kubernetes.io/cluster/chaos-cluster"]},
        {"Name": "tag-value", "Values": ["owned"]},
        {
            "Name": "tag-key",
            "Values": ["eksctl.cluster.k8s.io/v1alpha1/cluster-name"],
        },
    ]
    terminate_instances(filters=filters, az="us-west-2")

    called_filters = deepcopy(filters)
    called_filters.append(
        {"Name": "availability-zone", "Values": ["us-west-2"]}
    )
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.terminate_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_start_instances_by_id(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }
    start_instances(instance_ids=instance_ids)
    client.describe_instances.assert_called_with(InstanceIds=instance_ids)
    client.start_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_start_instances_by_filter(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-abcdef123456789"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }

    filters = [
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag-value", "Values": ["chaos-cluster"]},
        {"Name": "tag-key", "Values": ["kubernetes.io/cluster/chaos-cluster"]},
        {"Name": "tag-value", "Values": ["owned"]},
        {
            "Name": "tag-key",
            "Values": ["eksctl.cluster.k8s.io/v1alpha1/cluster-name"],
        },
    ]
    start_instances(filters=filters, az="us-west-2")

    called_filters = deepcopy(filters)
    called_filters.append(
        {"Name": "availability-zone", "Values": ["us-west-2"]}
    )
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.start_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_start_instances_by_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-abcdef123456789"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }
    start_instances(az="us-west-2")

    az_filter = [{"Name": "availability-zone", "Values": ["us-west-2"]}]
    client.describe_instances.assert_called_with(Filters=az_filter)
    client.start_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_restart_instances_by_id(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-392024ac3252ecb"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }
    restart_instances(instance_ids=instance_ids)
    client.describe_instances.assert_called_with(InstanceIds=instance_ids)
    client.reboot_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_restart_instances_by_filter(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-abcdef123456789"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }

    filters = [
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag-value", "Values": ["chaos-cluster"]},
        {"Name": "tag-key", "Values": ["kubernetes.io/cluster/chaos-cluster"]},
        {"Name": "tag-value", "Values": ["owned"]},
        {
            "Name": "tag-key",
            "Values": ["eksctl.cluster.k8s.io/v1alpha1/cluster-name"],
        },
    ]
    restart_instances(filters=filters, az="us-west-2")

    called_filters = deepcopy(filters)
    called_filters.append(
        {"Name": "availability-zone", "Values": ["us-west-2"]}
    )
    client.describe_instances.assert_called_with(Filters=called_filters)
    client.reboot_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_restart_instances_by_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba", "i-abcdef123456789"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_ids[0],
                        "InstanceLifecycle": "normal",
                    },
                    {
                        "InstanceId": instance_ids[1],
                        "InstanceLifecycle": "normal",
                    },
                ]
            }
        ]
    }
    restart_instances(az="us-west-2")

    az_filter = [{"Name": "availability-zone", "Values": ["us-west-2"]}]
    client.describe_instances.assert_called_with(Filters=az_filter)
    client.reboot_instances.assert_called_with(InstanceIds=instance_ids)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_detach_random_volume_ec2_id(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba"]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-987654321fedcba",
                        "BlockDeviceMappings": [
                            {
                                "DeviceName": "/dev/xvda",
                                "Ebs": {"VolumeId": "vol-00000001"},
                            },
                            {
                                "DeviceName": "/dev/sdc",
                                "Ebs": {"VolumeId": "vol-00000002"},
                            },
                        ],
                    }
                ]
            }
        ]
    }
    client.detach_volume.return_value = {
        "Device": "/dev/sdc",
        "InstanceId": "i-987654321fedcba",
        "State": "detaching",
        "VolumeId": "vol-00000002",
    }

    results = detach_random_volume(instance_ids=instance_ids)

    client.describe_instances.assert_called_with(
        InstanceIds=["i-987654321fedcba"]
    )
    client.detach_volume.assert_called_with(
        Device="/dev/sdc",
        Force=True,
        InstanceId="i-987654321fedcba",
        VolumeId="vol-00000002",
    )
    assert results[0]["Device"] == "/dev/sdc"


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_detach_random_volume_ec2_filter(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [
        {"Name": "block-device-mapping.device-name", "Values": ["/dev/sdb"]}
    ]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-987654321fedcba",
                        "BlockDeviceMappings": [
                            {
                                "DeviceName": "/dev/xvda",
                                "Ebs": {"VolumeId": "vol-00000001"},
                            },
                            {
                                "DeviceName": "/dev/sdb",
                                "Ebs": {"VolumeId": "vol-00000002"},
                            },
                        ],
                    }
                ]
            }
        ]
    }
    client.detach_volume.return_value = {
        "Device": "/dev/sdb",
        "InstanceId": "i-987654321fedcba",
        "State": "detaching",
        "VolumeId": "vol-00000002",
    }

    results = detach_random_volume(filters=filters)

    client.describe_instances.assert_called_with(Filters=filters)
    client.detach_volume.assert_called_with(
        Device="/dev/sdb",
        Force=True,
        InstanceId="i-987654321fedcba",
        VolumeId="vol-00000002",
    )
    assert results[0]["Device"] == "/dev/sdb"


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_detach_random_volume_ec2_invalid_id(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba"]
    client.describe_instances.return_value = {"Reservations": []}

    with pytest.raises(FailedActivity) as x:
        detach_random_volume(instance_ids=instance_ids)
    assert "no instances found matching: {'InstanceIds': %s}" % (
        instance_ids
    ) in str(x.value)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_detach_random_volume_ec2_invalid_filters(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [
        {"Name": "block-device-mapping.device-name", "Values": ["/dev/sdb"]}
    ]
    client.describe_instances.return_value = {"Reservations": []}

    with pytest.raises(FailedActivity) as x:
        detach_random_volume(filters=filters)
    assert "block-device-mapping.device-name" in str(x.value)
    assert "/dev/sdb" in str(x.value)


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_attach_volume_ec2_id(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba"]
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": [{"InstanceId": "i-987654321fedcba"}]}]
    }

    client.get_paginator.return_value.paginate.return_value = [
        {
            "Volumes": [
                {
                    "VolumeId": "vol-00000001",
                    "Tags": [
                        {
                            "Key": "ChaosToolkitDetached",
                            "Value": "DeviceName=/dev/sdc;InstanceId=%s"
                            % (instance_ids[0]),
                        }
                    ],
                },
                {
                    "VolumeId": "vol-00000002",
                    "Tags": [
                        {
                            "Key": "ChaosToolkitDetached",
                            "Value": "DeviceName=/dev/sdb;InstanceId="
                            "i-987654321fabcde",
                        }
                    ],
                },
            ]
        }
    ]

    client.attach_volume.return_value = {
        "DeviceName": "/dev/sdc",
        "InstanceId": instance_ids[0],
        "State": "attaching",
        "VolumeId": "vol-00000001",
    }

    results = attach_volume(instance_ids=instance_ids)

    client.describe_instances.assert_called_with(InstanceIds=instance_ids)
    client.get_paginator.return_value.paginate.assert_called_with(
        Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}]
    )
    client.attach_volume.assert_called_with(
        Device="/dev/sdc", InstanceId=instance_ids[0], VolumeId="vol-00000001"
    )
    assert results[0]["DeviceName"] == "/dev/sdc"


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_attach_volume_ec2_filter(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    instance_ids = ["i-987654321fedcba"]
    filters = [{"Name": "instance-state-name", "Values": ["running"]}]
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-987654321fedcba",
                        "State": {"Code": 16, "Name": "running"},
                    }
                ]
            }
        ]
    }

    client.get_paginator.return_value.paginate.return_value = [
        {
            "Volumes": [
                {
                    "VolumeId": "vol-00000001",
                    "Tags": [
                        {
                            "Key": "ChaosToolkitDetached",
                            "Value": "DeviceName=/dev/sdb;InstanceId=%s"
                            % (instance_ids[0]),
                        }
                    ],
                },
                {
                    "VolumeId": "vol-00000002",
                    "Tags": [
                        {
                            "Key": "ChaosToolkitDetached",
                            "Value": "DeviceName=/dev/sdb;InstanceId="
                            "i-987654321fabcde",
                        }
                    ],
                },
            ]
        }
    ]

    client.attach_volume.return_value = {
        "DeviceName": "/dev/sdb",
        "InstanceId": instance_ids[0],
        "State": "attaching",
        "VolumeId": "vol-00000001",
    }

    results = attach_volume(filters=filters)

    client.describe_instances.assert_called_with(Filters=filters)
    client.get_paginator.return_value.paginate.assert_called_with(
        Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}]
    )
    client.attach_volume.assert_called_with(
        Device="/dev/sdb", InstanceId=instance_ids[0], VolumeId="vol-00000001"
    )
    assert results[0]["DeviceName"] == "/dev/sdb"


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_authorize_security_group_ingress_with_ingress_security_group(
    aws_client,
):
    # arrange
    client = MagicMock()
    aws_client.return_value = client
    requested_security_group_id = "sg-123456789abc"
    ingress_security_group_id = "sg-123456789cba"
    ip_protocol = "tcp"
    from_port = 0
    to_port = 80
    # act
    authorize_security_group_ingress(
        requested_security_group_id=requested_security_group_id,
        ip_protocol=ip_protocol,
        from_port=from_port,
        to_port=to_port,
        ingress_security_group_id=ingress_security_group_id,
    )
    # assert
    client.authorize_security_group_ingress.assert_called_with(
        GroupId=requested_security_group_id,
        IpPermissions=[
            {
                "IpProtocol": ip_protocol,
                "FromPort": from_port,
                "ToPort": to_port,
                "IpRanges": [{}],
                "UserIdGroupPairs": [{"GroupId": ingress_security_group_id}],
            }
        ],
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_authorize_security_group_ingress_with_cidr_ip(aws_client):
    # arrange
    client = MagicMock()
    aws_client.return_value = client
    requested_security_group_id = "sg-123456789abc"
    cidr_ip = "0.0.0.0/0"
    ip_protocol = "tcp"
    from_port = 0
    to_port = 80
    # act
    authorize_security_group_ingress(
        requested_security_group_id=requested_security_group_id,
        ip_protocol=ip_protocol,
        from_port=from_port,
        to_port=to_port,
        cidr_ip=cidr_ip,
    )
    # assert
    client.authorize_security_group_ingress.assert_called_with(
        GroupId=requested_security_group_id,
        IpPermissions=[
            {
                "IpProtocol": ip_protocol,
                "FromPort": from_port,
                "ToPort": to_port,
                "IpRanges": [{"CidrIp": cidr_ip}],
                "UserIdGroupPairs": [{}],
            }
        ],
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_revoke_security_group_ingress_with_ingress_security_group(aws_client):
    # arrange
    client = MagicMock()
    aws_client.return_value = client
    requested_security_group_id = "sg-123456789abc"
    ingress_security_group_id = "sg-123456789cba"
    ip_protocol = "tcp"
    from_port = 0
    to_port = 80
    # act
    revoke_security_group_ingress(
        requested_security_group_id=requested_security_group_id,
        ip_protocol=ip_protocol,
        from_port=from_port,
        to_port=to_port,
        ingress_security_group_id=ingress_security_group_id,
    )
    # assert
    client.revoke_security_group_ingress.assert_called_with(
        GroupId=requested_security_group_id,
        IpPermissions=[
            {
                "IpProtocol": ip_protocol,
                "FromPort": from_port,
                "ToPort": to_port,
                "IpRanges": [{}],
                "UserIdGroupPairs": [{"GroupId": ingress_security_group_id}],
            }
        ],
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_revoke_security_group_ingress_with_cidr_ip(aws_client):
    # arrange
    client = MagicMock()
    aws_client.return_value = client
    requested_security_group_id = "sg-123456789abc"
    cidr_ip = "0.0.0.0/0"
    ip_protocol = "tcp"
    from_port = 0
    to_port = 80
    # act
    revoke_security_group_ingress(
        requested_security_group_id=requested_security_group_id,
        ip_protocol=ip_protocol,
        from_port=from_port,
        to_port=to_port,
        cidr_ip=cidr_ip,
    )
    # assert
    client.revoke_security_group_ingress.assert_called_with(
        GroupId=requested_security_group_id,
        IpPermissions=[
            {
                "IpProtocol": ip_protocol,
                "FromPort": from_port,
                "ToPort": to_port,
                "IpRanges": [{"CidrIp": cidr_ip}],
                "UserIdGroupPairs": [{}],
            }
        ],
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_set_tags_on_instances(aws_client):
    tags = "a=b,c=d"
    expected_tags = [{"Key": "a", "Value": "b"}, {"Key": "c", "Value": "d"}]

    client = MagicMock()
    aws_client.return_value = client
    inst_id_1 = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id_1, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    set_tags_on_instances(tags, percentage=10)

    client.create_tags.assert_called_with(
        Resources=[inst_id_1], Tags=expected_tags
    )


@patch("chaosaws.ec2.actions.aws_client", autospec=True)
def test_remove_tags_from_instances(aws_client):
    tags = "a=b,c=d"
    expected_tags = [{"Key": "a", "Value": "b"}, {"Key": "c", "Value": "d"}]

    client = MagicMock()
    aws_client.return_value = client
    inst_id_1 = "i-1234567890abcdef0"
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {"InstanceId": inst_id_1, "InstanceLifecycle": "normal"}
                ]
            }
        ]
    }

    remove_tags_from_instances(tags)

    client.delete_tags.assert_called_with(
        Resources=[inst_id_1], Tags=expected_tags
    )
