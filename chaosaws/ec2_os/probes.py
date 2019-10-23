# -*- coding: utf-8 -*-
import os
import time

from chaosaws import aws_client
from chaoslib.exceptions import FailedActivity
from chaosaws.types import AWSResponse
from chaoslib.types import Configuration, Secrets
from logzero import logger

from .actions import __get_os_type
from .constants import OS_LINUX,OS_WINDOWS

__all__ = ["describe_instance", "ensure_tc_installed", "ensure_tc_uninstalled"]


def describe_instance(instance_id: str,
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> AWSResponse:

    client = aws_client('ec2', configuration, secrets)

    return client.describe_instances(InstanceIds=[
        instance_id,
    ])


def ensure_tc_installed(instance_id: str,
                    configuration: Configuration = None,
                    secrets: Secrets = None) -> AWSResponse:
    __simple_ssm_helper(instance_id, configuration, secrets,
                        default_timeout=30,
                        script_name="ensure_tc_installed",
                        failure_matcher="Install iproute-tc package failed.")


def ensure_tc_uninstalled(instance_id: str,
                        configuration: Configuration = None,
                        secrets: Secrets = None) -> AWSResponse:
    __simple_ssm_helper(instance_id, configuration, secrets,
                        default_timeout=30,
                        script_name="ensure_tc_uninstalled",
                        failure_matcher="Remove iproute-tc package failed.")


###############################################################################
# Private helper functions
###############################################################################
def __simple_ssm_helper(instance_id: str,
                        configuration: Configuration = None,
                        secrets: Secrets = None,
                        default_timeout: int = 30,
                        script_name: str = None,
                        failure_matcher: str = "failed") -> AWSResponse:

    client = aws_client("ssm", configuration, secrets)
    if not instance_id:
        raise FailedActivity(
            "you must specify the instance_id"
        )
    try:
        if __get_os_type(instance_id, configuration, secrets) == "windows":
            os_type = OS_WINDOWS
            # TODO with PowerShell
            cmd = ""
            document_name = ""
        else:
            os_type = OS_LINUX
            document_name = "AWS-RunShellScript"
            with open(os.path.join(os.path.dirname(__file__),
                            "scripts", "{}.sh".format(script_name))) as file:
                script_content = file.read()

        res_send_command = client.send_command(
            InstanceIds=[instance_id],
            DocumentName=document_name,
            Parameters={
                'commands': [script_content]
            },
        )
        cmd_id = res_send_command["Command"]["CommandId"]
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
                            "Script exceeded default timeout {}"
                                .format(default_timeout))
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
                            "The result of command is considered failed:\n{}"
                                .format(failure_matcher))
                    logger.info("ssm run command status {}"
                                .format(invocation['Status']))
                    logger.info("ssm rum command result \n{}"
                                .format(invocation['Output'].rstrip('\n')))
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script:\n{}".format(x))
