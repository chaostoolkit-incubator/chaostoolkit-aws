# -*- coding: utf-8 -*-
from typing import Dict, List

import boto3
import random

from botocore.exceptions import ClientError
from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from logzero import logger

__all__ = ["suspend_processes", "resume_processes",
           "terminate_random_instances"]


def terminate_random_instances(asg_names: List[str] = None,
                               tags: List[Dict[str, str]] = None,
                               instance_count: int = None,
                               instance_percent: int = None,
                               az: str = None,
                               configuration: Configuration = None,
                               secrets: Secrets = None) -> List[AWSResponse]:
    """
    Terminates one or more random healthy instances associated to an ALB

    A healthy instance is considered one with a status of 'InService'

    Parameters:
            One Of:
                - asg_names: a list of one or more asg names to target
                - tags: a list of key/value pairs to identify the asgs by

            One Of:
                - instance_count: the number of instances to terminate
                - instance_percent: the percentage of instances to terminate
                - az: the availability zone to terminate instances

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if not any([instance_count, instance_percent, az]) or all(
            [instance_percent, instance_count, az]):
        raise FailedActivity(
            'Must specify one of "instance_count", "instance_percent", "az"')

    client = aws_client('autoscaling', configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    results = []
    for a in asgs['AutoScalingGroups']:
        # Filter out all instances not currently 'InService'
        instances = [e for e in a['Instances'] if e[
            'LifecycleState'] == 'InService']

        if az:
            instances = [e for e in instances if e['AvailabilityZone'] == az]

            if not instances:
                raise FailedActivity(
                    'No instances found in Availability Zone: {}'.format(az))
        else:
            if instance_percent:
                instance_count = int(float(
                    len(instances) * float(instance_percent)) / 100)

            if len(instances) < instance_count:
                raise FailedActivity(
                    'Not enough healthy instances in {} to satisfy '
                    'termination count {} ({})'.format(
                        a['AutoScalingGroupName'], instance_count,
                        len(instances)))

            instances = random.sample(instances, instance_count)

        client = aws_client('ec2', configuration, secrets)
        try:
            response = client.terminate_instances(
                InstanceIds=sorted([e['InstanceId'] for e in instances]))
            results.append({
                'AutoScalingGroupName': a['AutoScalingGroupName'],
                'TerminatingInstances': response['TerminatingInstances']})
        except ClientError as e:
            raise FailedActivity(e.response['Error']['Message'])
    return results


def suspend_processes(asg_names: List[str] = None,
                      tags: List[Dict[str, str]] = None,
                      process_names: List[str] = None,
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> AWSResponse:
    """
    Suspends 1 or more processes on a list of auto scaling groups.

    If no process is specified, all running auto scaling
    processes will be suspended.

    For a list of valid processes that can be suspended, reference:
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html

    Parameters:
        One of:
            - asg_names: a list of one or more asg names to target
            - tags: a list of key/value pairs to identify the asgs by

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if process_names:
        validate_processes(process_names)

    client = aws_client('autoscaling', configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs['AutoScalingGroups']:
        params = dict(AutoScalingGroupName=a['AutoScalingGroupName'])
        if process_names:
            params['ScalingProcesses'] = process_names

        logger.debug('Suspending process(es) on {}'.format(
            a["AutoScalingGroupName"]))
        client.suspend_processes(**params)

    return get_asg_by_name(
        [a['AutoScalingGroupName'] for a in asgs['AutoScalingGroups']], client)


def resume_processes(asg_names: List[str] = None,
                     tags: List[Dict[str, str]] = None,
                     process_names: List[str] = None,
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> AWSResponse:
    """
    Resumes 1 or more suspended processes on a list of auto scaling groups.

    If no process is specified, all suspended auto scaling
    processes will be resumed.

    For a list of valid processes that can be suspended, reference:
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html

    Parameters:
        One of:
            - asg_names: a list of one or more asg names to target
            - tags: a list of key/value pairs to identify the asgs by

    `tags` are expected as a list of dictionary objects:
    [
        {'Key': 'TagKey1', 'Value': 'TagValue1'},
        {'Key': 'TagKey2', 'Value': 'TagValue2'},
        ...
    ]
    """
    validate_asgs(asg_names, tags)

    if process_names:
        validate_processes(process_names)

    client = aws_client('autoscaling', configuration, secrets)

    if asg_names:
        asgs = get_asg_by_name(asg_names, client)
    else:
        asgs = get_asg_by_tags(tags, client)

    for a in asgs['AutoScalingGroups']:
        params = dict(AutoScalingGroupName=a['AutoScalingGroupName'])
        if process_names:
            params['ScalingProcesses'] = process_names

        logger.debug('Resuming process(es) {} on {}'.format(
            process_names, a['AutoScalingGroupName']))
        client.resume_processes(**params)

    return get_asg_by_name(
        [a['AutoScalingGroupName'] for a in asgs['AutoScalingGroups']], client)


###############################################################################
# Private functions
###############################################################################
def validate_asgs(asg_names: List[str] = None,
                  tags: List[Dict[str, str]] = None):
    if not any([asg_names, tags]):
        raise FailedActivity(
            'one of the following arguments are required: asg_names or tags')

    if all([asg_names, tags]):
        raise FailedActivity(
            'only one of the following arguments are allowed: asg_names/tags')


def get_asg_by_name(asg_names: List[str],
                    client: boto3.client) -> AWSResponse:
    logger.debug('Searching for ASG(s): {}.'.format(asg_names))

    asgs = client.describe_auto_scaling_groups(AutoScalingGroupNames=asg_names)

    if not asgs.get('AutoScalingGroups', []):
        raise FailedActivity(
            'Unable to locate ASG(s): {}'.format(asg_names))

    found_asgs = [a['AutoScalingGroupName'] for a in asgs['AutoScalingGroups']]
    invalid_asgs = [a for a in asg_names if a not in found_asgs]
    if invalid_asgs:
        raise FailedActivity('No ASG(s) found with name(s): {}'.format(
            invalid_asgs))
    return asgs


def get_asg_by_tags(tags: List[Dict[str, str]],
                    client: boto3.client) -> AWSResponse:
    params = []
    for t in tags:
        params.extend([
            {'Name': 'key', 'Values': [t['Key']]},
            {'Name': 'value', 'Values': [t['Value']]}])
    paginator = client.get_paginator('describe_tags')
    results = set()
    for p in paginator.paginate(Filters=tags):
        for a in p['Tags']:
            if a['ResourceType'] != 'auto-scaling-group':
                continue
            results.add(a['ResourceId'])

    if not results:
        raise FailedActivity(
            'No ASG(s) found with matching tag(s): {}.'.format(tags))
    return get_asg_by_name(list(results), client)


def validate_processes(process_names: List[str]):
    valid_processes = ['Launch', 'Terminate', 'HealthCheck', 'AZRebalance',
                       'AlarmNotification', 'ScheduledActions',
                       'AddToLoadBalancer', 'ReplaceUnhealthy']

    invalid_processes = [p for p in process_names if p not in valid_processes]
    if invalid_processes:
        raise FailedActivity('invalid process(es): {} not in {}.'.format(
            invalid_processes, valid_processes))
