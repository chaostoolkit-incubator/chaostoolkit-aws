# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from chaosaws.types import AWSResponse

import random
from chaosaws import aws_client


__all__ = ["stop_instance"]


def stop_instance(instance_id: str, force: bool = False,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Stop a given EC2 instance.
    """
    client = aws_client('ec2', configuration, secrets)
    return client.stop_instances(InstanceIds=[instance_id], Force=force)


def stop_random_instance(force: bool = False,
                         configuration: Configuration = None,
                         secrets: Secrets = None) -> AWSResponse:
    """
    Stop a random EC2 instance.
    """
    client = aws_client('ec2', configuration, secrets)
    res = client.describe_instances()
    x = random.randrange(0, len(res['Reservations']))
    instance_id = res['Reservations'][x]['Instances'][0]['InstanceId']
    return client.stop_instances(InstanceIds=[instance_id], Force=force)


def stop_random_instance_az(az: str, force: bool = False,
                            configuration: Configuration = None,
                            secrets: Secrets = None) -> AWSResponse:
    """
    Stop a random EC2 instance in a given availability zone.
    """
    client = aws_client('ec2', configuration, secrets)
    filters = [{'Name': 'availability-zone', 'Values': [az]}]
    res = client.describe_instances(Filters=filters)
    x = random.randrange(0, len(res['Reservations']))
    instance_id = res['Reservations'][x]['Instances'][0]['InstanceId']
    return client.stop_instances(InstanceIds=[instance_id], Force=force)


def stop_entire_az(az: str, force: bool = False,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Stop all EC2 instances in a given availability zone.
    """
    client = aws_client('ec2', configuration, secrets)
    filters = [{'Name': 'availability-zone', 'Values': [az]}]
    res = client.describe_instances(Filters=filters)
    instance_ids = []
    for subres in res['Reservations']:
        instance_ids.append(subres['Instances'][0]['InstanceId'])
    if instance_ids != []:
        return client.stop_instances(InstanceIds=instance_ids, Force=force)
    else:
        raise FailedActivity('No instances in the availability zone: ' + az)


def stop_instances(instance_ids, force: bool = False,
                   configuration: Configuration = None,
                   secrets: Secrets = None) -> AWSResponse:
    """
    Stop several given EC2 instance.
    """
    client = aws_client('ec2', configuration, secrets)
    return client.stop_instances(InstanceIds=instance_ids, Force=force)
