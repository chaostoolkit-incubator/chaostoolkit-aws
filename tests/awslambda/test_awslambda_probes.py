import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.awslambda.probes import (
    get_function_concurrency,
    get_function_memory_size,
    get_function_timeout,
    list_event_source_mapping,
)


def mock_client_error(operation_name: str):
    return ClientError(
        operation_name=operation_name,
        error_response={"Error": {"Message": "Test Error"}},
    )


def read_in_test_data(filename):
    module_path = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(module_path, "test_data", filename)
    with open(test_path) as fh:
        test_data = json.loads(fh.read())
    return test_data


@patch("chaosaws.awslambda.probes.aws_client", autospec=True)
def test_aws_lambda_get_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    get_function_concurrency(lambda_function_name)
    client.get_function_concurrency.assert_called_with(
        FunctionName=lambda_function_name
    )


@patch("chaosaws.awslambda.probes.aws_client", autospec=True)
def test_aws_lambda_get_function_timeout(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_function_configuration.return_value = {"Timeout": 3}
    lambda_function_name = "my-lambda-function"
    response = get_function_timeout(lambda_function_name)
    assert response == 3
    client.get_function_configuration.assert_called_with(
        FunctionName=lambda_function_name
    )


@patch("chaosaws.awslambda.probes.aws_client", autospec=True)
def test_aws_lambda_get_function_memory_size(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_function_configuration.return_value = {"MemorySize": 1024}
    lambda_function_name = "my-lambda-function"
    response = get_function_memory_size(lambda_function_name)
    assert response == 1024
    client.get_function_configuration.assert_called_with(
        FunctionName=lambda_function_name
    )


@patch("chaosaws.awslambda.probes.aws_client", autospec=True)
def test_aws_lambda_list_event_source_mappings(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_event_source_mappings.return_value = read_in_test_data(
        "list_event_source_mapping.json"
    )

    function_name = "GenericLambdaFunction"
    response = list_event_source_mapping(function_name=function_name)
    assert response["EventSourceMappings"]
    client.list_event_source_mappings.assert_called_with(
        FunctionName=function_name
    )


def test_aws_lambda_list_event_source_mappings_no_parameter():
    with pytest.raises(FailedActivity) as x:
        list_event_source_mapping()
    assert "must specify at least one of" in str(x)


@patch("chaosaws.awslambda.probes.aws_client", autospec=True)
def test_aws_lambda_list_event_source_mappings_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_event_source_mappings.side_effect = mock_client_error(
        "list_event_source_mappings"
    )

    with pytest.raises(FailedActivity) as x:
        function_name = "GenericLambdaFunction"
        list_event_source_mapping(function_name=function_name)
    assert "Test Error" in str(x)
