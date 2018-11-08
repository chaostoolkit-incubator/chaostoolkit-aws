# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
from chaosaws.cloudwatch.probes import get_alarm_state_value
from chaoslib.exceptions import FailedActivity
import pytest


@patch('chaosaws.cloudwatch.probes.aws_client', autospec=True)
def test_cloudwatch_get_alarm_state_value_ok(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alarm_name = 'my-alarm'
    client.describe_alarms.return_value = {
        'MetricAlarms': [
            {
                'AlarmName': alarm_name,
                'StateValue': 'OK'
            }
        ]
    }
    result = get_alarm_state_value(alarm_name)
    assert result == 'OK'
    client.describe_alarms.assert_called_with(AlarmNames=[alarm_name])


@patch('chaosaws.cloudwatch.probes.aws_client', autospec=True)
def test_cloudwatch_get_alarm_state_value_not_found(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    alarm_name = 'my-alarm'
    client.describe_alarms.return_value = {
        'MetricAlarms': []
    }
    with pytest.raises(FailedActivity):
        get_alarm_state_value(alarm_name)
    client.describe_alarms.assert_called_with(AlarmNames=[alarm_name])
