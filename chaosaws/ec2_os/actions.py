# -*- coding: utf-8 -*-
import time
from typing import Any, Dict, List

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse
from chaosaws.ec2_os import construct_script_content
from .probes import describe_os_type
from .constants import OS_LINUX, OS_WINDOWS
from .constants import BURN_CPU, FILL_DISK, NETWORK_UTIL, \
    BURN_IO, SSMDEFAULTNETWORKLAGACY, KILLALL_PROCESSES, KILL_PROCESS, RUN_CMD

__all__ = ["burn_cpu", "fill_disk", "network_latency", "burn_io",
           "network_loss", "network_corruption", "network_advanced",
           "os_advanced_internet_scripts", "killall_processes",
           "run_cmd", "kill_process"]


def burn_cpu(instance_ids: List[str] = None,
             execution_duration: str = "60",
             configuration: Configuration = None,
             secrets: Secrets = None) -> List[AWSResponse]:
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
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start burn_cpu: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=BURN_CPU,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def fill_disk(instance_ids: List[str] = None,
              execution_duration: str = "120",
              size: str = "1000",
              configuration: Configuration = None,
              secrets: Secrets = None) -> List[AWSResponse]:
    """
    For now do not have this scenario, fill the disk with random data.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    size : str
        Size of the file created on the disk. Defaults to 1000 MB.
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start fill_disk: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["size"] = size
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=FILL_DISK,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def burn_io(instance_ids: List[str] = None,
            execution_duration: str = "60",
            configuration: Configuration = None,
            secrets: Secrets = None) -> List[AWSResponse]:
    """
    Increases the Disk I/O operations per second of the virtual machine.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start burn_io: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=BURN_IO,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_advanced(instance_ids: List[str] = None,
                     execution_duration: str = "60",
                     command: str = "",
                     device: str = "eth0",
                     configuration: Configuration = None,
                     secrets: Secrets = None) -> List[AWSResponse]:
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
    command : str, optional
        advanced command line in tc, e.g. loss 5% or corrupt 10% etc.
    device : str, optional
        default to eth0, or specify the device name, e.g. enps0
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start network_advanced: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = command
            param["device"] = device
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=NETWORK_UTIL,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_loss(instance_ids: List[str] = None,
                 execution_duration: str = "60",
                 device: str = "eth0",
                 loss_ratio: str = "5%",
                 configuration: Configuration = None,
                 secrets: Secrets = None) -> List[AWSResponse]:
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
    device : str, optional
        default to eth0, or specify the device name, e.g. enps0
    loss_ratio : str:
        loss_ratio = "30%"
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start network_advanced: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "loss " + loss_ratio
            param["device"] = device
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=NETWORK_UTIL,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_corruption(instance_ids: List[str] = None,
                       execution_duration: str = "60",
                       device: str = "eth0",
                       corruption_ratio: str = "5%",
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> List[AWSResponse]:
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
    device : str, optional
        default to eth0, or specify the device name, e.g. enps0
    corruption_ratio : str:
        corruption_ratio = "30%"
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start network_corruption: configuration='{}', "
        "instance_ids='{}'".format(configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "corrupt " + corruption_ratio
            param["device"] = device
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=NETWORK_UTIL,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def network_latency(instance_ids: List[str] = None,
                    execution_duration: str = "60",
                    device: str = "eth0",
                    delay: str = "1000ms",
                    variance: str = "500ms",
                    ratio: str = "",
                    configuration: Configuration = None,
                    secrets: Secrets = None) -> List[AWSResponse]:
    """
    Increases the response time of the virtual machine.

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional
        Lifetime of the file created. Defaults to 120 seconds.
    device : str, optional
        default to eth0, or specify the device name, e.g. enps0
    delay : str
        Added delay in ms. Defaults to 1000ms.
    variance : str
        Variance of the delay in ms. Defaults to 500ms.
    ratio: str = "5%", optional
        the specific ratio of how many Variance of the delay in ms.
        Defaults to "".
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
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["param"] = "delay " + delay + " " + variance + " " + ratio
            param["device"] = device
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=NETWORK_UTIL,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def killall_processes(instance_ids: List[str] = None,
                      execution_duration: str = "1",
                      process_name: str = None,
                      signal: str = "",
                      configuration: Configuration = None,
                      secrets: Secrets = None) -> List[AWSResponse]:
    """
    The killall utility kills processes selected by name
    refer to https://linux.die.net/man/1/killall

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional default to 1 second
        This is not technically not useful as the process usually is killed
        without and delay, however you can set more seconds here to let the
        thread wait for more time to extend your experiment execution in case
        you need to watch more on the observation metrics.
    process_name : str
        Name of the process to be killed
    signal : str , default to ""
        The signal of killall command, e.g. use -9 to force kill
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
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["process_name"] = process_name
            param["signal"] = signal
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=KILLALL_PROCESSES,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def kill_process(instance_ids: List[str] = None,
                 execution_duration: str = "1",
                 process: str = None,
                 signal: str = "",
                 configuration: Configuration = None,
                 secrets: Secrets = None) -> List[AWSResponse]:
    """
    kill -s [signal_as_below] [processname]
    HUP INT QUIT ILL TRAP ABRT EMT FPE KILL BUS SEGV SYS PIPE ALRM TERM URG
    STOP TSTP CONT CHLD TTIN TTOU IO XCPU XFSZ VTALRM PROF WINCH INFO USR1 USR2

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional default to 1 second
        This is not technically not useful as the process usually is killed
        without and delay, however you can set more seconds here to let the
        thread wait for more time to extend your experiment execution in case
        you need to watch more on the observation metrics.
    process : str
        process or pid that kill command accetps
    signal : str , default to ""
        The signal of kill command, use kill -l for help
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
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["process_name"] = process
            param["signal"] = signal
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=KILL_PROCESS,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def run_cmd(instance_ids: List[str] = None,
            execution_duration: str = "60",
            cmd: List[str] = None,
            configuration: Configuration = None,
            secrets: Secrets = None) -> List[AWSResponse]:
    """
    run cmd
    Linus -> Shell
    Windows -> PowerShell

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    execution_duration : str, optional default to 1 second
        This is not technically not useful as the process usually is killed
        without and delay, however you can set more seconds here to let the
        thread wait for more time to extend your experiment execution in case
        you need to watch more on the observation metrics.
    cmd : List[str]
        Lines of your commands
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """

    logger.debug(
        "Start run_cmd: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))
    response = []
    try:
        for instance in instance_ids:
            param = dict()
            param["duration"] = execution_duration
            param["instance_id"] = instance
            param["cmd"] = cmd
            response.append(
                __linux_from_default(instance_id=instance,
                                     configuration=configuration,
                                     secrets=secrets,
                                     action=RUN_CMD,
                                     parameters=param)
            )
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script via AWS SSM {}".format(
                str(x)
            ))


def os_advanced_internet_scripts(instance_ids: List[str] = None,
                                 source_info: str = None,
                                 command_line: List[str] = None,
                                 execution_timeout: str = "60",
                                 configuration: Configuration = None,
                                 secrets: Secrets = None) -> List[AWSResponse]:
    """
    os_advanced_internet_scripts send commands

    Parameters
    ----------
    instance_ids : List[str]
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
    source_info : str
        Specify an URL that could be accessed from where your chaos runs.
        This function is supported by AWS SSM RunRemoteScript.
        You can specify either a public S3 address or a Github address.
        If your Github address requires login, you need also provide
        SSM secured parameter store.
        For example:
            "source_info": "https://s3.amazonaws.com/chaos/burnio.sh"
    command_line : str
        Specify the above script run command
        For example:
            "command_line": [ "burnio.sh -h param" ]
    execution_timeout : optional
        Default to 60 seconds
    configuration : Configuration
        Chaostoolkit Configuration
    secrets : Secrets
        Chaostoolkit Secrets
    """
    logger.debug(
        "Start network_latency: configuration='{}', instance_ids='{}'".format(
            configuration, instance_ids))

    try:
        return __linux_from_internet(instance_ids, source_info, command_line,
                                     execution_timeout, configuration, secrets)
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
                         secrets: Secrets = None) -> AWSResponse:

    default_timeout = int(parameters['duration'])
    client = aws_client("ssm", configuration, secrets)
    if not instance_id:
        raise FailedActivity(
            "you must specify the instance_id"
        )
    try:
        if describe_os_type(instance_id, configuration, secrets) == "windows":
            os_type = OS_WINDOWS
        else:
            os_type = OS_LINUX

        res_send_command = client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            # ===============================================
            # TODO if in Windows
            # DocumentName == 'AWS-RunPowerShellScript'
            # ===============================================
            Parameters={
                'commands':
                [construct_script_content(action, os_type, parameters)]
            },
        )
        cmd_id = res_send_command["Command"]["CommandId"]
        logger.info("ssm run command is sent, id {}".format(cmd_id))
        totalwait = 0
        interval = default_timeout / 2
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
                    interval = interval / 2 if interval > 1 else 1
                    if totalwait > default_timeout + SSMDEFAULTNETWORKLAGACY:
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
                    logger.info("ssm run command status {}"
                                .format(invocation['Status']))
                    logger.info("ssm rum command result \n{}"
                                .format(invocation['Output'].rstrip('\n')))
                    return invocation['Output'].rstrip('\n')
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script:\n{}".format(x))


def __linux_from_internet(instance_ids: List[str] = None,
                          source_info: str = None,
                          command_line: List[str] = None,
                          execution_timeout: str = "60",
                          configuration: Configuration = None,
                          secrets: Secrets = None) -> List[AWSResponse]:
    """
    Execute shell script on linux system
    """
    ssm_document = 'AWS-RunRemoteScript'
    sourceinfos = {"path": source_info}
    params = {"sourceType": ["S3"],
              "sourceInfo": [str(sourceinfos).replace('\'', '\"')],
              "executionTimeout": [execution_timeout],
              "commandLine": command_line}
    response = []
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
        logger.info("ssm run command is sent, id {}".format(cmd_id))
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
                # ===============================================
                # TODO if in Windows
                # if invocation['Name'] == 'runPowerShellScript':
                # ===============================================
                if invocation['Name'] == 'runShellScript':
                    logger.warning(invocation['Output'].rstrip('\n'))
                    response.append(invocation['Output'].rstrip('\n'))
        return response
    except Exception as x:
        raise FailedActivity(
            "failed issuing a execute of shell script：\n{}".format(x))
