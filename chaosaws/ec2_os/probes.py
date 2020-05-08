# -*- coding: utf-8 -*-
import time
from typing import List, Dict, Any

from chaosaws import aws_client
from chaoslib.exceptions import FailedActivity
from chaosaws.types import AWSResponse
from chaoslib.types import Configuration, Secrets
from logzero import logger

from .constants import OS_LINUX, OS_WINDOWS, GREP_PROCESS
from chaosaws.ec2_os import construct_script_content

__all__ = ["describe_os_type", "describe_instance",
           "ensure_tc_installed", "ensure_tc_uninstalled",
           "grep_process_exist"]


def describe_os_type(instance_id, configuration, secrets):
    res = describe_instance(instance_id, configuration, secrets)
    os = "linux"
    try:
        os = res['Reservations'][0]['Instances'][0]['Platform']
    except KeyError:
        logger.warning("No Platform key, so it is Linux")
    return os


def describe_instance(instance_id: str,
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> AWSResponse:

    client = aws_client('ec2', configuration, secrets)

    return client.describe_instances(InstanceIds=[
        instance_id,
    ])


def ensure_tc_installed(instance_ids: List[str] = None,
                        configuration: Configuration = None,
                        secrets: Secrets = None) -> List[AWSResponse]:
    response = []
    for instance_id in instance_ids:
        response.append(
            __simple_ssm_helper(
                instance_id=instance_id,
                configuration=configuration,
                secrets=secrets,
                default_timeout=30,
                action="ensure_tc_installed",
                failure_matcher="Install iproute-tc package failed."
            )
        )
    return response


def ensure_tc_uninstalled(instance_ids: List[str] = None,
                          configuration: Configuration = None,
                          secrets: Secrets = None) -> List[AWSResponse]:
    response = []
    for instance_id in instance_ids:
        response.append(
            __simple_ssm_helper(
                instance_id=instance_id,
                configuration=configuration,
                secrets=secrets,
                default_timeout=30,
                action="ensure_tc_uninstalled",
                failure_matcher="Remove iproute-tc package failed."
            )
        )
    return response


def grep_process_exist(instance_ids: List[str] = None,
                       process_name: str = None,
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> List[AWSResponse]:
    """
    Grep pid of process name

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    process_name : str
        Name of the process to be killed
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """
    logger.debug(
        "Start network_latency: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = "1"
            param["instance_id"] = instance
            param["process_name"] = process_name
            response.append(
                __simple_ssm_helper(instance_id=instance,
                                    configuration=configuration,
                                    secrets=secrets,
                                    action=GREP_PROCESS,
                                    parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


###############################################################################
# Private helper functions
###############################################################################
def __simple_ssm_helper(instance_id: str,
                        configuration: Configuration = None,
                        secrets: Secrets = None,
                        default_timeout: int = 30,
                        action: str = None,
                        parameters: Dict[str, Any] = None,
                        failure_matcher: str = "failed") -> AWSResponse:

    client = aws_client("ssm", configuration, secrets)
    if not instance_id:
        raise FailedActivity(
            "you must specify the instance_id"
        )
    try:
        if describe_os_type(instance_id, configuration, secrets) == "windows":
            os_type = OS_WINDOWS
            # TODO with PowerShell
            cmd = ""
            document_name = ""
        else:
            os_type = OS_LINUX
            document_name = "AWS-RunShellScript"

        res_send_command = client.send_command(
            InstanceIds=[instance_id],
            DocumentName=document_name,
            Parameters={
                'commands':
                    [construct_script_content(action, os_type, parameters)]
            },
        )
        cmd_id = res_send_command["Command"]["CommandId"]
        logger.info("ssm run command is sent, id {}".format(cmd_id))
        totalwait = 0
        interval = 1
        while True:
            res_list = client.list_command_invocations(
                CommandId=cmd_id,
                Details=True
            )
            try:
                cp = res_list['CommandInvocations'][0]['CommandPlugins'][0]
                status = cp['Status']
                if status == "InProgress":
                    time.sleep(interval)
                    totalwait += interval
                    if totalwait > default_timeout:
                        raise FailedActivity(
                            "Script exceeded default timeout {}".format(
                                default_timeout
                            )
                        )
                    continue
                elif status == "Failed":
                    break
                elif status == "Success":
                    break
                else:
                    break
            except IndexError:
                time.sleep(1)
                continue
        for command_invocation in res_list['CommandInvocations']:
            for invocation in command_invocation['CommandPlugins']:
                if invocation['Name'] == 'aws:runShellScript':
                    if failure_matcher in invocation['Output']:
                        raise FailedActivity(
                            "The result of command failed as:\n{}".format(
                                failure_matcher
                            )
                        )
                    logger.info("ssm run command status {}"
                                .format(invocation['Status']))
                    logger.info("ssm rum command result \n{}"
                                .format(invocation['Output'].rstrip('\n')))
                    return invocation['Output'].rstrip('\n')
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script:\n{}".format(x))
