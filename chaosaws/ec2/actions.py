# -*- coding: utf-8 -*-
import boto3
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse


__all__ = ["stop_instance"]


def stop_instance(instance_id: str, force: bool=False,
                  configuration: Configuration=None,
                  secrets: Secrets=None) -> AWSResponse:
    """
    Stop a given EC2 instance.
    """
    client = aws_client('ec2', configuration, secrets)
    return client.stop_instances(InstanceIds=[instance_id], Force=force)
