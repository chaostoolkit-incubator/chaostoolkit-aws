# -*- coding: utf-8 -*-
import json
from typing import Any, Dict

from botocore.exceptions import BotoCoreError
from botocore.errorfactory import BaseClientExceptions
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["attach_role_policy", "create_policy", "detach_role_policy"]


def create_policy(name: str, policy: Dict[str, Any], path: str = "/",
                  description: str = "", configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Create a new IAM policy
    """
    client = aws_client("iam", configuration, secrets)

    try:
        return client.create_policy(
            PolicyName=name,
            Path=path,
            PolicyDocument=json.dumps(policy),
            Description=description or ""
        )
    except Exception as x:
        raise FailedActivity(
            "failed creating a policy: {}".format(str(x)))


def attach_role_policy(arn: str, role_name: str,
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> AWSResponse:
    """
    Attach a role to a policy.
    """
    client = aws_client("iam", configuration, secrets)
    try:
        return client.attach_role_policy(PolicyArn=arn, RoleName=role_name)
    except Exception as x:
        raise FailedActivity(
            "failed attaching role '{}' to policy '{}': {}".format(
                role_name, arn, str(x)))


def detach_role_policy(arn: str, role_name: str,
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> AWSResponse:
    """
    Detach a role from a policy.
    """
    client = aws_client("iam", configuration, secrets)
    try:
        return client.detach_role_policy(PolicyArn=arn, RoleName=role_name)
    except Exception as x:
        raise FailedActivity(
            "failed detaching role '{}' from policy '{}': {}".format(
                role_name, arn, str(x)))
