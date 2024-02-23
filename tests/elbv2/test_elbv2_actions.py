from unittest.mock import MagicMock, call, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.elbv2.actions import (
    delete_load_balancer,
    deregister_target,
    enable_access_log,
    set_security_groups,
    set_subnets,
)


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_deregister_target(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    tg_name = "TestTargetGroup1"
    tg_arn = (
        "arn:aws:elasticloadbalancing:eu-west-1:111111111111:"
        "targetgroup/TestTargetGroup1/1234567890abcdef"
    )
    target_id = "i-0123456789abcdef0"
    client.describe_target_groups.return_value = {
        "TargetGroups": [{"TargetGroupArn": tg_arn, "TargetGroupName": tg_name}]
    }
    client.describe_target_health.return_value = {
        "TargetHealthDescriptions": [{"Target": {"Id": target_id, "Port": 80}}]
    }
    deregister_target(tg_name=tg_name)
    client.deregister_targets.assert_called_with(
        TargetGroupArn=tg_arn, Targets=[{"Id": target_id, "Port": 80}]
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_security_groups(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    security_group_ids = ["sg-0123456789abcdef0", "sg-0fedcba9876543210"]

    client.describe_security_groups.return_value = {
        "SecurityGroups": [
            {"GroupId": "sg-0123456789abcdef0"},
            {"GroupId": "sg-0fedcba9876543210"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            },
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-02/010aec0000fae123",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[1],
            },
        ]
    }
    set_security_groups(alb_names, security_group_ids)

    calls = [
        call(
            LoadBalancerArn="arn:aws:elasticloadbalancing:us-east-1:"
            "000000000000:loadbalancer/app/"
            "test-loadbalancer-01/0f158eab895ab000",
            SecurityGroups=security_group_ids,
        ),
        call(
            LoadBalancerArn="arn:aws:elasticloadbalancing:us-east-1:"
            "000000000000:loadbalancer/app/"
            "test-loadbalancer-02/010aec0000fae123",
            SecurityGroups=security_group_ids,
        ),
    ]
    client.set_security_groups.assert_has_calls(calls, any_order=True)


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_security_groups_invalid_alb_type(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    security_group_ids = ["sg-0123456789abcdef0", "sg-0fedcba9876543210"]

    client.describe_security_groups.return_value = {
        "SecurityGroups": [
            {"GroupId": "sg-0123456789abcdef0"},
            {"GroupId": "sg-0fedcba9876543210"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            },
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-02/010aec0000fae123",
                "State": {"Code": "active"},
                "Type": "network",
                "LoadBalancerName": alb_names[1],
            },
        ]
    }
    with pytest.raises(FailedActivity) as x:
        set_security_groups(alb_names, security_group_ids)
    assert "Cannot change security groups of network load balancers." in str(
        x.value
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_security_group_invalid_alb_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    security_group_ids = ["sg-0123456789abcdef0", "sg-0fedcba9876543210"]

    client.describe_security_groups.return_value = {
        "SecurityGroups": [
            {"GroupId": "sg-0123456789abcdef0"},
            {"GroupId": "sg-0fedcba9876543210"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        set_security_groups(alb_names, security_group_ids)
    assert f"Unable to locate load balancer(s): {[alb_names[1]]}" in str(
        x.value
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_security_groups_invalid_group(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    security_group_ids = ["sg-0123456789abcdef0", "sg-0fedcba9876543210"]

    client.describe_security_groups.return_value = {
        "SecurityGroups": [{"GroupId": "sg-0123456789abcdef0"}]
    }

    with pytest.raises(FailedActivity) as x:
        set_security_groups(alb_names, security_group_ids)
    assert f"Invalid security group id(s): {[security_group_ids[1]]}" in str(
        x.value
    )


def test_set_security_group_no_subnets():
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    with pytest.raises(TypeError) as x:
        set_security_groups(alb_names)
    assert (
        "set_security_groups() missing 1 required positional "
        "argument: 'security_group_ids'" in str(x.value)
    )


def test_set_security_group_no_args():
    with pytest.raises(TypeError) as x:
        set_security_groups()
    assert (
        "set_security_groups() missing 2 required positional arguments: "
        "'load_balancer_names' and 'security_group_ids" in str(x.value)
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_subnets(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    subnet_ids = ["subnet-012345678", "subnet-abcdefg0"]

    client.describe_subnets.return_value = {
        "Subnets": [
            {"SubnetId": "subnet-012345678"},
            {"SubnetId": "subnet-abcdefg0"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            },
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-02/010aec0000fae123",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[1],
            },
        ]
    }
    set_subnets(alb_names, subnet_ids)

    calls = [
        call(
            LoadBalancerArn="arn:aws:elasticloadbalancing:us-east-1:"
            "000000000000:loadbalancer/app/"
            "test-loadbalancer-01/0f158eab895ab000",
            Subnets=subnet_ids,
        ),
        call(
            LoadBalancerArn="arn:aws:elasticloadbalancing:us-east-1:"
            "000000000000:loadbalancer/app/"
            "test-loadbalancer-02/010aec0000fae123",
            Subnets=subnet_ids,
        ),
    ]
    client.set_subnets.assert_has_calls(calls, any_order=True)


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_subnets_invalid_alb_type(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    subnet_ids = ["subnet-012345678", "subnet-abcdefg0"]

    client.describe_subnets.return_value = {
        "Subnets": [
            {"SubnetId": "subnet-012345678"},
            {"SubnetId": "subnet-abcdefg0"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            },
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-02/010aec0000fae123",
                "State": {"Code": "active"},
                "Type": "network",
                "LoadBalancerName": alb_names[1],
            },
        ]
    }
    with pytest.raises(FailedActivity) as x:
        set_subnets(alb_names, subnet_ids)
    assert "Cannot change subnets of network load balancers." in str(x.value)


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_subnets_invalid_alb_name(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    subnet_ids = ["subnet-012345678", "subnet-abcdefg0"]

    client.describe_subnets.return_value = {
        "Subnets": [
            {"SubnetId": "subnet-012345678"},
            {"SubnetId": "subnet-abcdefg0"},
        ]
    }
    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:"
                "000000000000:loadbalancer/app/"
                "test-loadbalancer-01/0f158eab895ab000",
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            }
        ]
    }
    with pytest.raises(FailedActivity) as x:
        set_subnets(alb_names, subnet_ids)
    assert f"Unable to locate load balancer(s): {[alb_names[1]]}" in str(
        x.value
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_set_subnets_invalid_subnet(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    subnet_ids = ["subnet-012345678", "subnet-abcdefg0"]

    client.describe_subnets.return_value = {
        "Subnets": [{"SubnetId": "subnet-012345678"}]
    }

    with pytest.raises(FailedActivity) as x:
        set_subnets(alb_names, subnet_ids)
    assert f"Invalid subnet id(s): {[subnet_ids[1]]}" in str(x.value)


def test_set_subnet_no_subnets():
    alb_names = ["test-loadbalancer-01", "test-loadbalancer-02"]
    with pytest.raises(TypeError) as x:
        set_subnets(alb_names)

    assert (
        "set_subnets() missing 1 required "
        "positional argument: 'subnet_ids'" in str(x.value)
    )


def test_set_subnet_no_args():
    with pytest.raises(TypeError) as x:
        set_subnets()
    assert (
        "set_subnets() missing 2 required positional "
        "arguments: 'load_balancer_names' and 'subnet_ids'" in str(x.value)
    )


def test_delete_load_balancer_invalid():
    with pytest.raises(TypeError) as x:
        delete_load_balancer()
    assert (
        "delete_load_balancer() missing 1 required positional argument: "
        "'load_balancer_names'" in str(x.value)
    )


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_delete_load_balancr(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alb_names = ["test-loadbalancer-01"]
    lb_arn = (
        "arn:aws:elasticloadbalancing:us-east-1:"
        "000000000000:loadbalancer/app/"
        "test-loadbalancer-01/0f158eab895ab000"
    )

    client.describe_load_balancers.return_value = {
        "LoadBalancers": [
            {
                "LoadBalancerArn": lb_arn,
                "State": {"Code": "active"},
                "Type": "application",
                "LoadBalancerName": alb_names[0],
            }
        ]
    }
    delete_load_balancer(alb_names)

    client.describe_load_balancers.assert_called_with(Names=alb_names)
    client.delete_load_balancer.assert_called_with(LoadBalancerArn=lb_arn)


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_enable_access_log(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lb_arn = (
        "arn:aws:elasticloadbalancing:eu-west-1:111111111111:loadbalancer"
        "/app/test-lb/1234567890abcdef"
    )
    client.modify_load_balancer_attributes.return_value = {
        "Attributes": [
            {"Key": "access_logs.s3.enabled", "Value": "true"},
            {"Key": "access_logs.s3.bucket", "Value": "access-log-bucket"},
        ]
    }
    response = enable_access_log(
        load_balancer_arn=lb_arn, enable=True, bucket_name="access-log-bucket"
    )
    assert response is True


@patch("chaosaws.elbv2.actions.aws_client", autospec=True)
def test_disable_access_log(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lb_arn = (
        "arn:aws:elasticloadbalancing:eu-west-1:111111111111:loadbalancer"
        "/app/test-lb/1234567890abcdef"
    )
    client.modify_load_balancer_attributes.return_value = {
        "Attributes": [{"Key": "access_logs.s3.enabled", "Value": "false"}]
    }
    response = enable_access_log(load_balancer_arn=lb_arn)
    assert response is False
