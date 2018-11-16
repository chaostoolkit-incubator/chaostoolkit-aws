# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaosaws.awslambda.probes import (get_function_concurrency,
                                       get_function_memory_size,
                                       get_function_timeout)


@patch('chaosaws.awslambda.probes.aws_client', autospec=True)
def test_aws_lambda_get_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = 'my-lambda-function'
    get_function_concurrency(lambda_function_name)
    client.get_function.assert_called_with(FunctionName=lambda_function_name)


@patch('chaosaws.awslambda.probes.aws_client', autospec=True)
def test_aws_lambda_get_function_timeout(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_function_configuration.return_value = {
        'Timeout': 3
    }
    lambda_function_name = 'my-lambda-function'
    response = get_function_timeout(lambda_function_name)
    assert response == 3
    client.get_function_configuration.assert_called_with(
        FunctionName=lambda_function_name
    )


@patch('chaosaws.awslambda.probes.aws_client', autospec=True)
def test_aws_lambda_get_function_memory_size(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_function_configuration.return_value = {
        'MemorySize': 1024
    }
    lambda_function_name = 'my-lambda-function'
    response = get_function_memory_size(lambda_function_name)
    assert response == 1024
    client.get_function_configuration.assert_called_with(
        FunctionName=lambda_function_name
    )
