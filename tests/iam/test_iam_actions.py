import json
from unittest.mock import MagicMock, patch

from chaosaws.iam.actions import (
    attach_role_policy,
    create_policy,
    detach_role_policy,
)


@patch("chaosaws.iam.actions.aws_client", autospec=True)
def test_create_policy(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "logs:CreateLogGroup",
                "Resource": "RESOURCE_ARN",
            }
        ],
    }

    create_policy("mypolicy", policy, "/user/Jon")
    client.create_policy.assert_called_with(
        PolicyName="mypolicy",
        Path="/user/Jon",
        PolicyDocument=json.dumps(policy),
        Description="",
    )


@patch("chaosaws.iam.actions.aws_client", autospec=True)
def test_attach_role_policy(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    arn = "aws:iam:whatever"
    role = "somerole"
    attach_role_policy(arn, role)
    client.attach_role_policy.assert_called_with(PolicyArn=arn, RoleName=role)


@patch("chaosaws.iam.actions.aws_client", autospec=True)
def test_detach_role_policy(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    arn = "aws:iam:whatever"
    role = "somerole"
    detach_role_policy(arn, role)
    client.detach_role_policy.assert_called_with(PolicyArn=arn, RoleName=role)
