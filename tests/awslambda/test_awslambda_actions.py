# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.awslambda.actions import put_function_concurrency
from chaosaws.awslambda.actions import delete_function_concurrency


@patch('chaosaws.awslambda.actions.aws_client', autospec=True)
def test_aws_lambda_put_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = 'my-lambda-function'
    concurrency = 0
    put_function_concurrency(lambda_function_name, concurrency)
    client.put_function_concurrency.assert_called_with(FunctionName=lambda_function_name,
                                                       ReservedConcurrentExecutions=concurrency)

@patch('chaosaws.awslambda.actions.aws_client', autospec=True)
def test_aws_lambda_put_function_concurrency_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = ''
    concurrency = 0
    with pytest.raises(FailedActivity):
        put_function_concurrency(lambda_function_name, concurrency)


@patch('chaosaws.awslambda.actions.aws_client', autospec=True)
def test_aws_lambda_put_function_concurrency_failedactivity(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = 'my-lambda-function'
    concurrency = 0

    with patch.object(client, 'put_function_concurrency', FailedActivity):
        with pytest.raises(Exception):
            put_function_concurrency(lambda_function_name, concurrency)


@patch('chaosaws.awslambda.actions.aws_client', autospec=True)
def test_aws_lambda_delete_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = 'my-lambda-function'
    delete_function_concurrency(lambda_function_name)
    client.delete_function_concurrency.assert_called_with(FunctionName=lambda_function_name)
