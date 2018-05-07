# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["describe_instances"]


def describe_instances(filters: List[Dict[str, Any]],
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> AWSResponse:
    """
    Describe instances following the specified filters.

    Please refer to http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    for details on said filters.
    """  # noqa: E501
    client = aws_client('ec2', configuration, secrets)
    return client.describe_instances(Filters=filters)
