# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, mock_open, call

from chaosaws.ec2_os.actions import burn_cpu, fill_disk, network_latency, \
    burn_io, network_loss, network_corruption, network_advanced, \
    os_advanced_internet_scripts, killall_processes, kill_process


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


CONFIG = {
    "aws": {
        "aws_region": "cn-north-1"
    }
}

SECRETS = {
    "aws": {
        "aws_access_key_id": "abcdefghijklmn",
        "aws_secret_access_key": "opqrstuvwxyz",
        "aws_session_token": "abcdefghijklmnopqrstuvwxyz",
    }
}

INSTANCE_IDS = ["i-04cf7749ff48ca517"]

CMD_ID_RETURN = {
    'Command': {
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'DocumentName': 'AWS-RunShellScript',
        'DocumentVersion': '',
        'Comment': ''
    }
}

CMD_LIST_INVOCATION_RETURN = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'InstanceName': '',
        'Comment': '',
        'DocumentName': 'AWS-RunShellScript',
        'DocumentVersion': '',
        'RequestedDateTime': None,
        'Status': 'Success',
        'StatusDetails': 'Success',
        'StandardOutputUrl': '',
        'StandardErrorUrl': '',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'Stressing i-04cf7749ff48ca517 2 CPUs for 90 seconds.\nStressing 2 CPUs for 90 seconds. Done\nexperiment strees_cpu <i-04cf7749ff48ca517> -> success\n',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }],
        'ServiceRole': '',
        'NotificationConfig': {
            'NotificationArn': '',
            'NotificationEvents': [],
            'NotificationType': ''
        },
        'CloudWatchOutputConfig':{
            'CloudWatchLogGroupName': '',
            'CloudWatchOutputEnabled': False
        }
    }],
    'ResponseMetadata': {
        'RequestId': 'b3f724e7-8ca2-4198-9483-d5b2dff3119a',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': 'b3f724e7-8ca2-4198-9483-d5b2dff3119a',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '998',
            'date': 'Wed, 23 Oct 2019 05:01:48 GMT'
        },
        'RetryAttempts': 0
    }
}

CMD_LIST_INVOCATION_REMOTE_RETURN = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'InstanceName': '',
        'Comment': '',
        'DocumentName': 'AWS-RunRemoteScript',
        'DocumentVersion': '',
        'RequestedDateTime': None,
        'Status': 'Success',
        'StatusDetails': 'Success',
        'StandardOutputUrl': '',
        'StandardErrorUrl': '',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'Stressing i-04cf7749ff48ca517 2 CPUs for 90 seconds.\nStressing 2 CPUs for 90 seconds. Done\nexperiment strees_cpu <i-04cf7749ff48ca517> -> success\n',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }],
        'ServiceRole': '',
        'NotificationConfig': {
            'NotificationArn': '',
            'NotificationEvents': [],
            'NotificationType': ''
        },
        'CloudWatchOutputConfig':{
            'CloudWatchLogGroupName': '',
            'CloudWatchOutputEnabled': False
        }
    }],
    'ResponseMetadata': {
        'RequestId': 'b3f724e7-8ca2-4198-9483-d5b2dff3119a',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': 'b3f724e7-8ca2-4198-9483-d5b2dff3119a',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '998',
            'date': 'Wed, 23 Oct 2019 05:01:48 GMT'
        },
        'RetryAttempts': 0
    }
}

CMD_RETURN_DISK = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'experiment fill_disk -> <i-04cf7749ff48ca517>: success',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }]
    }]
}

CMD_RETURN_NETWORK = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'experiment network (loss 5%) -> <i-04cf7749ff48ca517>: success',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }]
    }]
}

CMD_RETURN_PROCESSES = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'experiment killall_processes -> processes <java> on <i-04cf7749ff48ca517>: success',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }]
    }]
}

CMD_RETURN_PROCESS = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'experiment kill_process -> process <java> on <i-04cf7749ff48ca517>: success',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }]
    }]
}

CMD_RETURN_FAIL = {
    'CommandInvocations': [{
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'InstanceId': 'i-04cf7749ff48ca517',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'Success',
            'StatusDetails': 'Success',
            'ResponseCode': 0,
            'ResponseStartDateTime': None,
            'ResponseFinishDateTime': None,
            'Output': 'experiment network (corruption 15%) -> <i-04cf7749ff48ca517>: fail',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': 'cn-north-1',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }]
    }]
}

CMD_RETURN_IN_PROGRESS = {
    'CommandInvocations': [{
        'CommandId': '015c2722-9004-40cb-a4d2-871fec1e00d7',
        'InstanceId': 'i-04cf7749ff48ca517',
        'InstanceName': '',
        'Comment': '',
        'DocumentName': 'AWS-RunShellScript',
        'DocumentVersion': '',
        'RequestedDateTime': None,
        'Status': 'InProgress',
        'StatusDetails': 'InProgress',
        'StandardOutputUrl': '',
        'StandardErrorUrl': '',
        'CommandPlugins': [{
            'Name': 'aws:runShellScript',
            'Status': 'InProgress',
            'StatusDetails': 'InProgress',
            'ResponseCode': -1,
            'Output': '',
            'StandardOutputUrl': '',
            'StandardErrorUrl': '',
            'OutputS3Region': '',
            'OutputS3BucketName': '',
            'OutputS3KeyPrefix': ''
        }],
        'ServiceRole': '',
        'NotificationConfig': {
            'NotificationArn': '',
            'NotificationEvents': [],
            'NotificationType': ''
        },
        'CloudWatchOutputConfig': {
            'CloudWatchLogGroupName': '',
            'CloudWatchOutputEnabled': False
        }}],
    'ResponseMetadata': {
        'RequestId': 'fe1562ae-1e37-499a-9159-7bcff451d431',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': 'fe1562ae-1e37-499a-9159-7bcff451d431',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '769',
            'date': 'Wed, 23 Oct 2019 05:29:03 GMT'
        }, 'RetryAttempts': 0
    }}

CMD_REMOTE = {
    "CommandInvocations": [
        {
            "CommandId": "e2296cff-b479-4240-8645-f1e84350d054",
            "InstanceId": "i-04cf7749ff48ca517",
            "InstanceName": "u7000nec2oapk8s0002",
            "Comment": "",
            "DocumentName": "AWS-RunRemoteScript",
            "DocumentVersion": "",
            "RequestedDateTime": 1571984830.578,
            "Status": "Success",
            "StatusDetails": "Success",
            "StandardOutputUrl": "",
            "StandardErrorUrl": "",
            "CommandPlugins": [
                {
                    "Name": "downloadContent",
                    "Status": "Success",
                    "StatusDetails": "Success",
                    "ResponseCode": 0,
                    "ResponseStartDateTime": 1571984831.032,
                    "ResponseFinishDateTime": 1571984831.226,
                    "Output": "",
                    "StandardOutputUrl": "",
                    "StandardErrorUrl": "",
                    "OutputS3Region": "cn-north-1",
                    "OutputS3BucketName": "",
                    "OutputS3KeyPrefix": ""
                },
                {
                    "Name": "runPowerShellScript",
                    "Status": "Success",
                    "StatusDetails": "Success",
                    "ResponseCode": 0,
                    "ResponseStartDateTime": 1571984831.226,
                    "ResponseFinishDateTime": 1571984831.226,
                    "Output": "Step execution skipped due to incompatible platform. Step name: runPowerShellScript",
                    "StandardOutputUrl": "",
                    "StandardErrorUrl": "",
                    "OutputS3Region": "cn-north-1",
                    "OutputS3BucketName": "",
                    "OutputS3KeyPrefix": ""
                },
                {
                    "Name": "runShellScript",
                    "Status": "Success",
                    "StatusDetails": "Success",
                    "ResponseCode": 0,
                    "ResponseStartDateTime": 1571984831.227,
                    "ResponseFinishDateTime": 1571984831.236,
                    "Output": "experiment steady state -> <i-04cf7749ff48ca517>: success",
                    "StandardOutputUrl": "",
                    "StandardErrorUrl": "",
                    "OutputS3Region": "cn-north-1",
                    "OutputS3BucketName": "",
                    "OutputS3KeyPrefix": ""
                }
            ],
            "ServiceRole": "",
            "NotificationConfig": {
                "NotificationArn": "",
                "NotificationEvents": [],
                "NotificationType": ""
            },
            "CloudWatchOutputConfig": {
                "CloudWatchLogGroupName": "",
                "CloudWatchOutputEnabled": False
            }
        }
    ]
}


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_burn_cpu(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_LIST_INVOCATION_RETURN

    os_type.return_value = "Linux"

    list_res = burn_cpu(instance_ids=INSTANCE_IDS, execution_duration="30",
                        configuration=CONFIG, secrets=SECRETS)

    open.assert_called_with(AnyStringWith("cpu_stress_test.sh"))
    assert "success" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment strees_cpu" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_fill_disk(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_DISK

    os_type.return_value = "Linux"

    list_res = fill_disk(instance_ids=INSTANCE_IDS, execution_duration="30",
                         size="5000", configuration=CONFIG, secrets=SECRETS)

    open.assert_called_with(AnyStringWith("fill_disk.sh"))
    assert "success" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment fill_disk" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_kill_process(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_PROCESS

    os_type.return_value = "Linux"

    list_res = kill_process(instance_ids=INSTANCE_IDS,
                            execution_duration="30",
                            signal="-9",
                            process="java",
                            configuration=CONFIG,
                            secrets=SECRETS)

    open.assert_called_with(AnyStringWith("kill_process.sh"))
    assert "success" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment kill_process" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_network(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_NETWORK

    os_type.return_value = "Linux"

    list_res = network_latency(instance_ids=INSTANCE_IDS,
                               execution_duration="30",
                               configuration=CONFIG,
                               delay="1000ms",
                               variance="500ms",
                               ratio="50%",
                               secrets=SECRETS)

    open.assert_called_with(AnyStringWith("network_advanced.sh"))
    assert "success" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment network" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_network_fail(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_FAIL

    os_type.return_value = "Linux"

    list_res = network_corruption(instance_ids=INSTANCE_IDS,
                                  execution_duration="30",
                                  configuration=CONFIG,
                                  corruption_ratio="50%",
                                  secrets=SECRETS)

    open.assert_called_with(AnyStringWith("network_advanced.sh"))
    assert "fail" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment network" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_burn_io_timeout(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_IN_PROGRESS

    os_type.return_value = "Linux"

    with pytest.raises(Exception) as ex:
        list_res = burn_io(instance_ids=INSTANCE_IDS,
                           execution_duration="2",
                           configuration=CONFIG,
                           secrets=SECRETS)
    assert 'Script exceeded default timeout' in str(ex.value)
    open.assert_called_with(AnyStringWith("burn_io.sh"))


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_network_exception(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_IN_PROGRESS

    os_type.return_value = "Linux"

    with pytest.raises(Exception) as ex:
        list_res = network_advanced(instance_ids=INSTANCE_IDS,
                                    execution_duration="2",
                                    configuration=CONFIG,
                                    command="loss 100%",
                                    device="eth0",
                                    secrets=SECRETS)
    assert 'failed issuing a execute of shell script via AWS SSM' in str(ex.value)
    open.assert_called_with(AnyStringWith("network_advanced.sh"))


@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_os_advanced_internet_scripts(aws_client, os_type):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_REMOTE

    os_type.return_value = "Linux"

    list_res = os_advanced_internet_scripts(instance_ids=INSTANCE_IDS,
                                            source_info="https://s3.aws/test.sh",
                                            command_line=["sh test.sh"],
                                            configuration=CONFIG,
                                            execution_timeout="5",
                                            secrets=SECRETS)
    assert "success" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment steady state" in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.actions.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.actions.aws_client', autospec=True)
def test_killall_processes(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_RETURN_PROCESSES

    os_type.return_value = "Linux"

    list_res = killall_processes(instance_ids=INSTANCE_IDS,
                                 execution_duration="30",
                                 process_name="java",
                                 signal="-9",
                                 configuration=CONFIG,
                                 secrets=SECRETS)

    open.assert_called_with(AnyStringWith("killall_processes.sh"))
    assert "success" in list_res[0]
    assert "java" in list_res[0]
    assert INSTANCE_IDS[0] in list_res[0]
    assert "experiment killall_processes" in list_res[0]