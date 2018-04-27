# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client

__all__ = ["get_policy"]


def get_policy(arn: str, configuration: Configuration = None,
               secrets: Secrets = None) -> bool:
    """
    Get a policy by its ARN
    """
    client = aws_client("iam", configuration, secrets)
    return client.get_policy(PolicyArn=arn)
