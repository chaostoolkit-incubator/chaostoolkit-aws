from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.asg.actions import (
    attach_volume,
    change_subnets,
    detach_random_instances,
    detach_random_volume,
    resume_processes,
    stop_random_instances,
    suspend_processes,
    terminate_random_instances,
)


def test_suspend_process_no_name_or_tag():
    with pytest.raises(FailedActivity) as x:
        suspend_processes()
    assert (
        "one of the following arguments are required: "
        "asg_names or tags" in str(x.value)
    )


def test_suspend_process_both_name_and_tag_one():
    with pytest.raises(FailedActivity) as x:
        suspend_processes(
            asg_names=["AutoScalingGroup-A"],
            tags=[{"Key": "TagKey", "Values": ["TagValues"]}],
        )
    assert (
        "only one of the following arguments are allowed: "
        "asg_names/tags" in str(x.value)
    )


def test_suspend_process_invalid_process():
    with pytest.raises(FailedActivity) as x:
        suspend_processes(
            asg_names=["AutoScalingGroup-A"], process_names=["Lunch"]
        )
    assert "invalid process(es): ['Lunch'] not in" in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_suspend_process_asg_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [],
            }
        ]
    }
    suspend_processes(asg_names=asg_names)
    client.suspend_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0]
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_suspend_process_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [],
            }
        ]
    }
    suspend_processes(tags=[{"Key": "TargetKey", "Value": "TargetValue"}])
    client.suspend_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0]
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_suspend_process_asg_invalid_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {"AutoScalingGroups": []}
    with pytest.raises(FailedActivity) as x:
        suspend_processes(asg_names=asg_names, process_names=["Launch"])
    assert "Unable to locate ASG(s): %s" % asg_names in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_suspend_process_asg_invalid_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A", "AutoScalingGroup-B"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        suspend_processes(asg_names=asg_names, process_names=["Launch"])
    assert "No ASG(s) found with name(s): %s" % ([asg_names[1]]) in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_suspend_process_asg_invalid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [{"Tags": []}]
    with pytest.raises(FailedActivity) as x:
        suspend_processes(tags=tags)
    assert "No ASG(s) found with matching tag(s): %s." % tags in str(x.value)


def test_resume_process_no_name_or_tag():
    with pytest.raises(FailedActivity) as x:
        resume_processes()
    assert (
        "one of the following arguments are required: "
        "asg_names or tags" in str(x.value)
    )


def test_resume_process_both_name_and_tag():
    with pytest.raises(FailedActivity) as x:
        resume_processes(
            asg_names=["AutoScalingGroup-A"],
            tags=[{"Key": "TagKey", "Values": ["TagValues"]}],
        )
    assert (
        "only one of the following arguments are allowed: "
        "asg_names/tags" in str(x.value)
    )


def test_resume_process_invalid_process():
    with pytest.raises(FailedActivity) as x:
        resume_processes(
            asg_names=["AutoScalingGroup-A"], process_names=["Lunch"]
        )
    assert "invalid process(es): ['Lunch'] not in" in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_resume_process_asg_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [{"ProcessName": "Launch"}],
            }
        ]
    }
    resume_processes(asg_names=asg_names, process_names=["Launch"])
    client.resume_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0], ScalingProcesses=["Launch"]
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_resume_process_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [{"ProcessName": "Launch"}],
            }
        ]
    }
    resume_processes(tags=tags, process_names=["Launch"])
    client.resume_processes.assert_called_with(
        AutoScalingGroupName=asg_names[0], ScalingProcesses=["Launch"]
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_resume_process_asg_invalid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [{"Tags": []}]
    with pytest.raises(FailedActivity) as x:
        resume_processes(tags=tags)
    assert "No ASG(s) found with matching tag(s): %s." % tags in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_resume_process_asg_invalid_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {"AutoScalingGroups": []}
    with pytest.raises(FailedActivity) as x:
        resume_processes(asg_names=asg_names, process_names=["Launch"])
    assert "Unable to locate ASG(s): " in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_resume_process_asg_invalid_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A", "AutoScalingGroup-B"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "DesiredCapacity": 1,
                "Instances": [
                    {"HealthStatus": "Healthy", "LifecycleState": "InService"}
                ],
                "SuspendedProcesses": [{"ProcessName": "Launch"}],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        resume_processes(asg_names=asg_names, process_names=["Launch"])
    assert "No ASG(s) found with name(s): %s" % ([asg_names[1]]) in str(x.value)


def test_terminate_instances_no_asgs():
    with pytest.raises(FailedActivity) as x:
        terminate_random_instances(instance_count=10)
    assert (
        "one of the following arguments are required: "
        "asg_names or tags" in str(x.value)
    )


def test_terminate_instances_no_numbers():
    asg_names = ["AutoScalingGroup-A", "AutoScalingGroup-B"]
    with pytest.raises(FailedActivity) as x:
        terminate_random_instances(asg_names)
    assert (
        'Must specify one of "instance_count", '
        '"instance_percent", "az"' in str(x.value)
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_count_pass(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    terminate_random_instances(asg_names=asg_names, instance_count=2)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    for i in instance_calls:
        try:
            client.terminate_instances.assert_called_with(InstanceIds=sorted(i))
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_percent_pass(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    terminate_random_instances(asg_names=asg_names, instance_percent=50)

    instance_calls = [
        "i-00000000000000001",
        "i-00000000000000002",
        "i-00000000000000003",
    ]

    ex = None
    for i in instance_calls:
        try:
            client.terminate_instances.assert_called_with(InstanceIds=[i])
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_valid_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    terminate_random_instances(asg_names=asg_names, az="us-east-1a")
    client.terminate_instances.assert_called_with(
        InstanceIds=["i-00000000000000001"]
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_invalid_az(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        terminate_random_instances(asg_names=asg_names, az="us-east-1d")
    assert "No instances found in Availability Zone: us-east-1d" in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_invalid_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    }
                ],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        terminate_random_instances(asg_names=asg_names, instance_count=2)
    assert (
        "Not enough healthy instances in {} to satisfy "
        "termination count {} ({})".format(asg_names[0], 2, 1)
        in str(x.value)
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_terminate_instances_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    terminate_random_instances(tags=tags, instance_count=2)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    for i in instance_calls:
        try:
            client.terminate_instances.assert_called_with(InstanceIds=sorted(i))
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


def test_detach_instance_no_name_or_tag():
    with pytest.raises(FailedActivity) as x:
        detach_random_instances()
    assert (
        "one of the following arguments are required: "
        "asg_names or tags" in str(x.value)
    )


def test_detach_instance_both_name_and_tag_one():
    with pytest.raises(FailedActivity) as x:
        detach_random_instances(
            asg_names=["AutoScalingGroup-A"],
            tags=[{"Key": "TagKey", "Values": ["TagValues"]}],
        )
    assert (
        "only one of the following arguments are allowed: "
        "asg_names/tags" in str(x.value)
    )


def test_detach_instance_no_count():
    with pytest.raises(FailedActivity) as x:
        detach_random_instances(asg_names=["AutoScalingGroup-A"])
    assert (
        'You must specify either "instance_count" or '
        '"instance_percent"' in str(x.value)
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_instances_invalid_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        detach_random_instances(asg_names, instance_count=3)
    assert (
        "You are attempting to detach more instances than exist on "
        "asg %s" % asg_names[0] in str(x.value)
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_instances_count(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    result = detach_random_instances(asg_names, instance_count=2)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    call_found = False
    for i in instance_calls:
        try:
            call_found = False
            instance_ids = sorted(i)
            client.detach_instances.assert_called_with(
                AutoScalingGroupName=asg_names[0],
                InstanceIds=instance_ids,
                ShouldDecrementDesiredCapacity=False,
            )
            call_found = True
            assert result["DetachingInstances"] == [
                {
                    "AutoScalingGroupName": asg_names[0],
                    "InstanceIds": instance_ids,
                }
            ]
            return None
        except AssertionError as e:
            ex = str(e.args)
            if call_found:
                break
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_instances_percent(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    detach_random_instances(asg_names, instance_percent=67)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    for i in instance_calls:
        try:
            client.detach_instances.assert_called_with(
                AutoScalingGroupName=asg_names[0],
                InstanceIds=sorted(i),
                ShouldDecrementDesiredCapacity=False,
            )
            return None
        except AssertionError as e:
            ex = str(e.args)
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_instances_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    detach_random_instances(tags=tags, instance_count=2)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    for i in instance_calls:
        try:
            client.detach_instances.assert_called_with(
                AutoScalingGroupName="AutoScalingGroup-A",
                InstanceIds=sorted(i),
                ShouldDecrementDesiredCapacity=False,
            )
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_change_subnets_valid_names(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    params = dict(
        asg_names=asg_names, subnets=["subnet-123456789", "subnet-23456789a"]
    )
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "VPCZoneIdentifier": "subnet-012345678,subnet-123456789",
            }
        ]
    }
    change_subnets(**params)
    client.update_auto_scaling_group.assert_called_with(
        AutoScalingGroupName=asg_names[0],
        VPCZoneIdentifier="subnet-123456789,subnet-23456789a",
    )


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_change_subnets_valid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    params = dict(tags=tags, subnets=["subnet-123456789", "subnet-23456789a"])
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "VPCZoneIdentifier": "subnet-012345678,subnet-123456789",
            }
        ]
    }
    change_subnets(**params)

    client.update_auto_scaling_group.assert_called_with(
        AutoScalingGroupName="AutoScalingGroup-A",
        VPCZoneIdentifier="subnet-123456789,subnet-23456789a",
    )


def test_change_subnets_no_subnet():
    asg_names = ["AutoScalingGroup-A"]
    with pytest.raises(TypeError) as x:
        change_subnets(asg_names=asg_names)
    assert "missing 1 required positional argument: 'subnets'" in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_random_volume_asg_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [{"InstanceId": "i-00000000000000001"}],
            }
        ]
    }
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
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
        "InstanceId": "i-00000000000000001",
        "State": "detaching",
        "VolumeId": "vol-00000002",
    }

    results = detach_random_volume(asg_names=asg_names)

    client.describe_auto_scaling_groups.assert_called_with(
        AutoScalingGroupNames=asg_names
    )
    client.describe_instances.assert_called_with(
        InstanceIds=["i-00000000000000001"]
    )
    client.detach_volume.assert_called_with(
        Device="/dev/sdc",
        Force=True,
        InstanceId="i-00000000000000001",
        VolumeId="vol-00000002",
    )
    assert results[0]["Device"] == "/dev/sdc"


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_random_volume_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [{"InstanceId": "i-00000000000000001"}],
            }
        ]
    }
    client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
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
        "InstanceId": "i-00000000000000001",
        "State": "detaching",
        "VolumeId": "vol-00000002",
    }

    results = detach_random_volume(tags=tags)

    client.describe_auto_scaling_groups.assert_called_with(
        AutoScalingGroupNames=asg_names
    )
    client.describe_instances.assert_called_with(
        InstanceIds=["i-00000000000000001"]
    )
    client.detach_volume.assert_called_with(
        Device="/dev/sdb",
        Force=True,
        InstanceId="i-00000000000000001",
        VolumeId="vol-00000002",
    )
    assert results[0]["Device"] == "/dev/sdb"


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_random_volume_asg_invalid_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {"AutoScalingGroups": []}

    with pytest.raises(FailedActivity) as x:
        detach_random_volume(asg_names=asg_names)
    assert "Unable to locate ASG(s): %s" % asg_names in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_detach_random_volume_asg_invalid_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.describe_instances.return_value = {"Reservations": []}

    with pytest.raises(FailedActivity) as x:
        detach_random_volume(tags=tags)
    assert "No ASG(s) found with matching tag(s): %s" % tags in str(x.value)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_attach_volume_asg_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": asg_names[0],
                "Instances": [{"InstanceId": "i-00000000000000001"}],
            }
        ]
    }

    client.describe_volumes.return_value = {
        "Volumes": [
            {
                "VolumeId": "vol-00000001",
                "Tags": [
                    {
                        "Key": "ChaosToolkitDetached",
                        "Value": "DeviceName=/dev/sdc;InstanceId=%s;ASG=%s"
                        % ("i-987654321fabcde", asg_names[0]),
                    }
                ],
            },
            {
                "VolumeId": "vol-00000002",
                "Tags": [
                    {
                        "Key": "ChaosToolkitDetached",
                        "Value": "DeviceName=/dev/sdb;InstanceId="
                        "i-987654321fefghi",
                    }
                ],
            },
        ]
    }

    client.attach_volume.return_value = {
        "DeviceName": "/dev/sdc",
        "InstanceId": "i-987654321fabcde",
        "State": "attaching",
        "VolumeId": "vol-00000001",
    }

    results = attach_volume(asg_names=asg_names)

    client.describe_auto_scaling_groups.assert_called_with(
        AutoScalingGroupNames=asg_names
    )
    client.describe_volumes.assert_called_with(
        Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}]
    )
    client.attach_volume.assert_called_with(
        Device="/dev/sdc",
        InstanceId="i-987654321fabcde",
        VolumeId="vol-00000001",
    )
    assert results[0]["DeviceName"] == "/dev/sdc"


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_attach_volume_asg_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": asg_names[0],
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": asg_names[0],
                "Instances": [{"InstanceId": "i-00000000000000001"}],
            }
        ]
    }

    client.describe_volumes.return_value = {
        "Volumes": [
            {
                "VolumeId": "vol-00000001",
                "Tags": [
                    {
                        "Key": "ChaosToolkitDetached",
                        "Value": "DeviceName=/dev/sdb;InstanceId=%s;ASG=%s"
                        % ("i-00000000000000001", asg_names[0]),
                    }
                ],
            },
            {
                "VolumeId": "vol-00000002",
                "Tags": [
                    {
                        "Key": "ChaosToolkitDetached",
                        "Value": "DeviceName=/dev/sdb;InstanceId="
                        "i-987654321fghij",
                    }
                ],
            },
        ]
    }

    client.attach_volume.return_value = {
        "DeviceName": "/dev/sdb",
        "InstanceId": "i-00000000000000001",
        "State": "attaching",
        "VolumeId": "vol-00000001",
    }

    results = attach_volume(tags=tags)

    client.describe_auto_scaling_groups.assert_called_with(
        AutoScalingGroupNames=asg_names
    )
    client.get_paginator.return_value.paginate.assert_called_with(
        Filters=[
            {"Name": "key", "Values": ["TargetKey"]},
            {"Name": "value", "Values": ["TargetValue"]},
        ]
    )
    client.describe_volumes.assert_called_with(
        Filters=[{"Name": "tag-key", "Values": ["ChaosToolkitDetached"]}]
    )
    client.attach_volume.assert_called_with(
        Device="/dev/sdb",
        InstanceId="i-00000000000000001",
        VolumeId="vol-00000001",
    )
    assert results[0]["DeviceName"] == "/dev/sdb"


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_asg_stop_random_instance_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    asg_names = ["AutoScalingGroup-A"]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    stop_random_instances(asg_names=asg_names, instance_percent=50)

    instance_calls = [
        "i-00000000000000001",
        "i-00000000000000002",
        "i-00000000000000003",
    ]

    ex = None
    for i in instance_calls:
        try:
            client.stop_instances.assert_called_with(
                Force=False, InstanceIds=[i]
            )
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)


@patch("chaosaws.asg.actions.aws_client", autospec=True)
def test_asg_stop_random_instance_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tags = [{"Key": "TargetKey", "Value": "TargetValue"}]
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Tags": [
                {
                    "ResourceId": "AutoScalingGroup-A",
                    "ResourceType": "auto-scaling-group",
                    "Key": "TargetKey",
                    "Value": "TargetValue",
                    "PropagateAtLaunch": False,
                }
            ]
        }
    ]
    client.describe_auto_scaling_groups.return_value = {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "AutoScalingGroup-A",
                "Instances": [
                    {
                        "InstanceId": "i-00000000000000001",
                        "AvailabilityZone": "us-east-1a",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000002",
                        "AvailabilityZone": "us-east-1b",
                        "LifecycleState": "InService",
                    },
                    {
                        "InstanceId": "i-00000000000000003",
                        "AvailabilityZone": "us-east-1c",
                        "LifecycleState": "InService",
                    },
                ],
            }
        ]
    }
    stop_random_instances(tags=tags, instance_count=2)

    instance_calls = [
        ["i-00000000000000001", "i-00000000000000002"],
        ["i-00000000000000001", "i-00000000000000003"],
        ["i-00000000000000002", "i-00000000000000003"],
    ]

    ex = None
    for i in instance_calls:
        try:
            client.stop_instances.assert_called_with(
                Force=False, InstanceIds=sorted(i)
            )
            return None
        except AssertionError as e:
            ex = e.args
    raise AssertionError(ex)
