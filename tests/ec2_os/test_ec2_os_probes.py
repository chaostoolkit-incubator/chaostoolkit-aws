# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, mock_open, call

from chaosaws.ec2_os.probes import describe_instance, describe_os_type, \
                                   ensure_tc_installed, ensure_tc_uninstalled


CONFIG = {
    "aws": {
        "aws_region": "cn-north-1"
    }
}

INSTANCE_IDS = ["i-04cf7749ff48ca517"]

SECRETS = {
    "aws": {
        "aws_access_key_id": "abcdefghijklmn",
        "aws_secret_access_key": "opqrstuvwxyz",
        "aws_session_token": "abcdefghijklmnopqrstuvwxyz",
    }
}

CMD_ID_RETURN = {
    'Command': {
        'CommandId': '6ff4cc59-dac6-4d2e-8952-8ac53930627a',
        'DocumentName': 'AWS-RunShellScript',
        'DocumentVersion': '',
        'Comment': ''
    }
}

INSTANCE_DESC = {
    'Reservations': [{
        'Instances': [{
            'InstanceId': 'i-1234567890abcdef0',
            'InstanceLifecycle': 'spot',
            'SpotInstanceRequestId': 'sir-abcdef01'}]}]}

INSTANCE_DESC_WINDOWS = {
    'Reservations': [{
        'Instances': [{
            'InstanceId': 'i-1234567890abcdef0',
            'Platform': 'Windows',
            'InstanceLifecycle': 'spot',
            'SpotInstanceRequestId': 'sir-abcdef01'}]}]}

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
            'Output': '',
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


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_describe_os_type(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = INSTANCE_DESC

    os = describe_os_type(instance_id='i-1234567890abcdef0', secrets=SECRETS,
                          configuration=CONFIG)
    assert "linux" == os


@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_describe_os_type_windows(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = INSTANCE_DESC_WINDOWS

    os = describe_os_type(instance_id='i-1234567890abcdef0', secrets=SECRETS,
                          configuration=CONFIG)
    assert "Windows" == os


@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_describe_instances_windows(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = INSTANCE_DESC_WINDOWS

    response = describe_instance(instance_id='i-1234567890abcdef0',
                                 secrets=SECRETS,
                                 configuration=CONFIG)
    assert INSTANCE_DESC_WINDOWS == response


@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_describe_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.describe_instances.return_value = INSTANCE_DESC

    response = describe_instance(instance_id='i-1234567890abcdef0',
                                 secrets=SECRETS,
                                 configuration=CONFIG)
    assert INSTANCE_DESC == response


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.probes.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_ensure_tc_installed(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_LIST_INVOCATION_RETURN

    os_type.return_value = "Linux"

    list_res = ensure_tc_installed(instance_ids=INSTANCE_IDS,
                                   configuration=CONFIG,
                                   secrets=SECRETS)
    open.assert_called_with(AnyStringWith("ensure_tc_installed.sh"))
    assert "failed" not in list_res[0]


@patch("builtins.open", new_callable=mock_open, read_data="script")
@patch('chaosaws.ec2_os.probes.describe_os_type', autospec=True)
@patch('chaosaws.ec2_os.probes.aws_client', autospec=True)
def test_ensure_tc_uninstalled(aws_client, os_type, open):
    client = MagicMock()
    aws_client.return_value = client
    client.send_command.return_value = CMD_ID_RETURN
    client.list_command_invocations.return_value = CMD_LIST_INVOCATION_RETURN

    os_type.return_value = "Linux"

    list_res = ensure_tc_uninstalled(instance_ids=INSTANCE_IDS,
                                     configuration=CONFIG,
                                     secrets=SECRETS)
    open.assert_called_with(AnyStringWith("ensure_tc_uninstalled.sh"))
    assert "failed" not in list_res[0]
