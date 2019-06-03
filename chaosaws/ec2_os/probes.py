# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.types import Configuration, Secrets

__all__ = ["describe_instance"]


def describe_instance(instance_id: str,
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> AWSResponse:

    client = aws_client('ec2', configuration, secrets)

    return client.describe_instances(InstanceIds=[
        instance_id,
    ])

