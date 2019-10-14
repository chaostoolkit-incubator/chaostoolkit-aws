# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

from typing import Any, Dict, List
from logzero import logger
import time
import os
from .probes import describe_instance
from .constants import OS_LINUX, OS_WINDOWS
from .constants import BURN_CPU, FILL_DISK, NETWORK_UTIL, \
    BURN_IO, SSMDEFAULTNETWORKLAGACY

__all__ = ["burn_cpu", "fill_disk", "network_latency", "burn_io",
           "network_loss", "network_corruption", "network_advanced",
           "os_advanced"]


def burn_cpu(instance_ids: List[str] = None,
             execution_duration: str = "60",
             configuration: Configuration = None,
             secrets: Secrets = None):
    """
    burn CPU up to 100% at random machines.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Duration of the stress test (in seconds) that generates high CPU usage.
        Defaults to 60 seconds.
    """

    logger.debug(
        "Start burn_cpu: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=BURN_CPU,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def fill_disk(instance_ids: List[str] = None,
              execution_duration: str = "120",
              size: int = 1000,
              configuration: Configuration = None,
              secrets: Secrets = None):
    """
    For now do not have this scenario, fill the disk with random data.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    size : int
        Size of the file created on the disk. Defaults to 1GB.
    """

    logger.debug(
        "Start fill_disk: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["size"] = size
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=FILL_DISK,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def burn_io(instance_ids: List[str] = None,
            execution_duration: str = "60",
            configuration: Configuration = None,
            secrets: Secrets = None):
    """
    Increases the Disk I/O operations per second of the virtual machine.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    """

    logger.debug(
        "Start burn_io: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=BURN_IO,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_advanced(instance_ids: List[str] = None,
                     execution_duration: str = "60",
                     command: str = "",
                     configuration: Configuration = None,
                     secrets: Secrets = None):
    """
    do a customized operations on the virtual machine via Linux - TC.
    For windows, no solution as for now.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 60 seconds.
    """

    logger.debug(
        "Start network_advanced: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = command
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=NETWORK_UTIL,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_loss(instance_ids: List[str] = None,
                 execution_duration: str = "60",
                 loss_ratio: str = "5%",
                 configuration: Configuration = None,
                 secrets: Secrets = None):
    """
    do a network loss operations on the virtual machine via Linux - TC.
    For windows, no solution as for now.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 60 seconds.
    loss_ratio : str:
        loss_ratio = "30%"
    """

    logger.debug(
        "Start network_advanced: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "loss " + loss_ratio
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=NETWORK_UTIL,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_corruption(instance_ids: List[str] = None,
                       execution_duration: str = "60",
                       corruption_ratio: str = "5%",
                       configuration: Configuration = None,
                       secrets: Secrets = None):
    """
    do a network loss operations on the virtual machine via Linux - TC.
    For windows, no solution as for now.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 60 seconds.
    corruption_ratio : str:
        corruption_ratio = "30%"
    """

    logger.debug(
        "Start network_corruption: configuration='{}', "
        "instance_ids='{}'".format(configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "corrupt " + corruption_ratio
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=NETWORK_UTIL,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_latency(instance_ids: List[str] = None,
                    execution_duration: str = "60",
                    delay: str = "1000ms",
                    variance: str = "500ms",
                    ratio: str = "",
                    configuration: Configuration = None,
                    secrets: Secrets = None):
    """
    Increases the response time of the virtual machine.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    delay : str
        Added delay in ms. Defaults to 1000ms.
    variance : str
        Variance of the delay in ms. Defaults to 500ms.
    ratio: str = "5%", optional
        the specific ratio of how many Variance of the delay in ms.
        Defaults to "".
    """
    logger.debug(
        "Start network_latency: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "delay " + delay + " " + variance + " " + ratio
            __linux_from_default(instance_id=instance,
                                 configuration=configuration,
                                 secrets=secrets,
                                 action=NETWORK_UTIL,
                                 parameters=param)
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def os_advanced(instance_ids: List[str] = None,
                source_info: str = None,
                command_line: List[str] = None,
                execution_timeout: str = "60",
                configuration: Configuration = None,
                secrets: Secrets = None) -> AWSResponse:
    """
    os_advanced send commands
    """
    logger.debug(
        "Start network_latency: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        __linux_from_internet(instance_ids, source_info, command_line,
                              execution_timeout, configuration , secrets )
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


###############################################################################
# Private helper functions
###############################################################################
def __linux_from_default(instance_id: str = None,
                         action: str = None,
                         parameters: Dict[str, Any] = None,
                         configuration: Configuration = None,
                         secrets: Secrets = None) -> List[AWSResponse]:

    default_timeout = int(parameters['duration'])
    client = aws_client("ssm", configuration, secrets)
    if not instance_id:
        raise FailedActivity(
            "you must specify the instance_id"
        )
    try:
        if __get_os_type(instance_id, configuration, secrets) == "windows":
            os_type = OS_WINDOWS
        else:
            os_type = OS_LINUX
        res_send_command = client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands':
                [__construct_script_content__(action, os_type, parameters)]
            },
        )
        logger.debug(res_send_command)
        cmd_id = res_send_command["Command"]["CommandId"]
        totalwait = 0
        interval = default_timeout / 2
        while True:
            res_list = client.list_command_invocations(
                CommandId=cmd_id,
                Details=True
            )
            logger.debug(res_list)
            try:
                cp = res_list['CommandInvocations'][0]['CommandPlugins'][0]
                status = cp['Status']
                if status == "InProgress" :
                    time.sleep(interval)
                    totalwait += interval
                    interval = interval / 2 if interval > 1 else 1
                    if totalwait > default_timeout + SSMDEFAULTNETWORKLAGACY:
                        raise FailedActivity(
                            "Script exceeded default timeout {}"
                            .format(default_timeout))
                    continue
                elif status == "Failed" :
                    break
                elif status == "Success" :
                    break
                else :
                    break
            except IndexError:
                time.sleep(1)
                continue
        for command_invocation in res_list['CommandInvocations']:
            for invocation in command_invocation['CommandPlugins']:
                if invocation['Name'] == 'aws:runShellScript':
                    logger.info("ssm run command status {}"
                                .format(invocation['Status']))
                    logger.info("ssm rum command result \n{}"
                                .format(invocation['Output'].rstrip('\n')))
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script:\n{}".format(x))


def __linux_from_internet(instance_ids: List[str] = None,
                          source_info: str = None,
                          command_line: List[str] = None,
                          execution_timeout: str = "60",
                          configuration: Configuration = None,
                          secrets: Secrets = None) -> AWSResponse:
    """
    Execute shell script on linux system
    """
    ssm_document = 'AWS-RunRemoteScript'
    sourceinfos = {"path": source_info}
    params = {"sourceType": ["S3"],
              "sourceInfo": [str(sourceinfos).replace('\'', '\"')],
              "executionTimeout": [execution_timeout],
              "commandLine": command_line}

    client = aws_client("ssm", configuration, secrets)
    if not instance_ids:
        raise FailedActivity(
            "you must specify the instance_id"
        )
    try:
        res_send_command = client.send_command(
            InstanceIds=instance_ids,
            DocumentName=ssm_document,
            Parameters=params
        )
        cmd = res_send_command['Command']
        cmd_id = cmd['CommandId']
        while True:
            res_list = client.list_command_invocations(
                CommandId=cmd_id,
                Details=True
            )
            cmd_invocations = str(res_list['CommandInvocations'])
            if cmd_invocations.find("runShellScript") == -1:
                time.sleep(0.1)
                continue
            else:
                break
        for command_invocation in res_list['CommandInvocations']:
            for invocation in command_invocation['CommandPlugins']:
                if invocation['Name'] == 'runShellScript':
                    logger.warning(invocation['Output'].rstrip('\n'))
                    return
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script")


def __construct_script_content__(action, os_type, parameters):

    if os_type == OS_WINDOWS:
        script_name = action+".ps1"
        # TODO in ps1
        cmd_param = '\n'.join(
            ['='.join([k, "'"+v+"'"]) for k, v in parameters.items()])
    elif os_type == OS_LINUX:
        script_name = action+".sh"
        cmd_param = '\n'.join(
            ['='.join([k, "'"+v+"'"]) for k, v in parameters.items()])
    else:
        raise FailedActivity(
            "Cannot find corresponding script for {} on OS: {}".format(
                action, os_type))

    with open(os.path.join(os.path.dirname(__file__),
                           "scripts", script_name)) as file:
        script_content = file.read()
    # merge duration
    script_content = cmd_param + "\n" + script_content
    return script_content


def __get_os_type(instance_id, configuration, secret):
    res = describe_instance(instance_id, configuration, secret)
    os = "linux"
    try:
        os = res['Reservations'][0]['Instances'][0]['Platform']
    except KeyError:
        logger.warning("No Platform key, so it is Linux")
    return os