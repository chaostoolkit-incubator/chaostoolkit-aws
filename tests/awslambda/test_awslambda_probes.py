# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
from chaosaws.awslambda.probes import get_function_concurrency


@patch('chaosaws.awslambda.probes.aws_client', autospec=True)
def test_aws_lambda_get_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = 'my-lambda-function'
    get_function_concurrency(lambda_function_name)
    client.get_function.assert_called_with(FunctionName=lambda_function_name)
