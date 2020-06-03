# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
from tests.zpharmacy import Pharmacy
from chaosaws.cloudwatch.actions import (
    put_rule, put_rule_targets, disable_rule, enable_rule, delete_rule,
    remove_rule_targets, set_alarm_state)
from chaosaws.cloudwatch.probes import get_alarm_state_value


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_put_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    schedule_expression = 'rate(5 minutes)'
    state = 'ENABLED'
    description = 'My 5 minute rule'
    role_arn = 'iam:role:for:my:rule'
    put_rule(rule_name,
                        schedule_expression=schedule_expression,
                        state=state,
                        description=description,
                        role_arn=role_arn)
    client.put_rule.assert_called_with(
        Name=rule_name,
        ScheduleExpression=schedule_expression,
        State=state,
        Description=description,
        RoleArn=role_arn)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_put_rule_targets(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    targets = [
        {
            'Id': '1234',
            'Arn': 'arn:aws:lambda:eu-central-1:'
            '101010101010:function:MyFunction'
        }
    ]
    put_rule_targets(rule_name, targets)
    client.put_targets.assert_called_with(Rule=rule_name, Targets=targets)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_disable_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    disable_rule(rule_name)
    client.disable_rule.assert_called_with(Name=rule_name)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_enable_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    enable_rule(rule_name)
    client.enable_rule.assert_called_with(Name=rule_name)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_delete_rule(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    delete_rule(rule_name)
    client.delete_rule.assert_called_with(Name=rule_name)
    client.remove_targets.assert_not_called()


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_delete_rule_force(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    target_ids = ['1', '2', '3']
    client.list_targets_by_rule.return_value = {
        'Targets': [{'Id': t} for t in target_ids]
    }
    rule_name = 'my-rule'
    delete_rule(rule_name, force=True)
    client.delete_rule.assert_called_with(Name=rule_name)
    client.list_targets_by_rule.assert_called_with(Rule=rule_name)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_remove_rule_targets(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    target_ids = ['1', '2', '3']
    remove_rule_targets(rule_name, target_ids)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


@patch('chaosaws.cloudwatch.actions.aws_client', autospec=True)
def test_cloudwatch_remove_rule_targets_all(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    rule_name = 'my-rule'
    target_ids = ['1', '2', '3']
    client.list_targets_by_rule.return_value = {
        'Targets': [{'Id': t} for t in target_ids]
    }
    remove_rule_targets(rule_name, target_ids=None)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)
    client.list_targets_by_rule.assert_called_with(Rule=rule_name)
    client.remove_targets.assert_called_with(Rule=rule_name, Ids=target_ids)


class TestCloudWatchActions(Pharmacy):
    def test_set_cloudwatch_alarm(self):
        session = self.replay_data('test_set_cloudwatch_alarm')
        params = {
            'alarm_name': 'MyTempTest',
            'alarm_state': 'ALARM',
            'configuration': {
                'aws_session': session, 'aws_region': 'us-east-1'}}

        set_alarm_state(**params)

        params.pop('alarm_state')

        results = get_alarm_state_value(**params)
        self.assertEqual(results, 'ALARM')
