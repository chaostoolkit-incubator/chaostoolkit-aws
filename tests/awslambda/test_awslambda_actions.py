import json
import os
from base64 import b64encode
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.awslambda.actions import (
    delete_event_source_mapping,
    delete_function_concurrency,
    invoke_function,
    put_function_concurrency,
    put_function_memory_size,
    put_function_timeout,
    toggle_event_source_mapping_state,
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


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_put_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    concurrency = 0
    put_function_concurrency(lambda_function_name, concurrency)
    client.put_function_concurrency.assert_called_with(
        FunctionName=lambda_function_name,
        ReservedConcurrentExecutions=concurrency,
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_put_function_concurrency_empty_string(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = ""
    concurrency = 0
    with pytest.raises(FailedActivity):
        put_function_concurrency(lambda_function_name, concurrency)


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_put_function_concurrency_failedactivity(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    concurrency = 0

    with patch.object(client, "put_function_concurrency", FailedActivity):
        with pytest.raises(Exception):
            put_function_concurrency(lambda_function_name, concurrency)


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_delete_function_concurrency(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    delete_function_concurrency(lambda_function_name)
    client.delete_function_concurrency.assert_called_with(
        FunctionName=lambda_function_name
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_invoke_no_args(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    mock_payload = {"some": "response"}
    mock_response = {"Payload": MagicMock()}
    mock_response["Payload"].read.return_value = json.dumps(
        mock_payload
    ).encode()
    client.invoke.return_value = mock_response
    lambda_function_name = "my-lambda-function"

    response = invoke_function(lambda_function_name)

    assert response["Payload"] == mock_payload
    client.invoke.assert_called_with(
        FunctionName=lambda_function_name,
        InvocationType="RequestResponse",
        LogType="None",
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_invoke_with_args(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    mock_payload = {"some": "response"}
    mock_response = {"Payload": MagicMock()}
    mock_response["Payload"].read.return_value = json.dumps(
        mock_payload
    ).encode()
    client.invoke.return_value = mock_response
    lambda_function_name = "my-lambda-function"
    function_arguments = {"some": "argument"}
    invocation_type = "Event"
    client_context = {"some": "context"}
    qualifier = "$LATEST"

    invoke_function(
        function_name=lambda_function_name,
        function_arguments=function_arguments,
        invocation_type=invocation_type,
        client_context=client_context,
        qualifier=qualifier,
    )

    client.invoke.assert_called_with(
        FunctionName=lambda_function_name,
        InvocationType=invocation_type,
        LogType="None",
        Payload=json.dumps(function_arguments),
        ClientContext=b64encode(json.dumps(client_context).encode()).decode(),
        Qualifier=qualifier,
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_invoke_failed(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.invoke.side_effect = Exception("Some Exception")
    lambda_function_name = "my-lambda-function"
    with pytest.raises(FailedActivity):
        invoke_function(lambda_function_name)
    client.invoke.assert_called_with(
        FunctionName=lambda_function_name,
        InvocationType="RequestResponse",
        LogType="None",
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_invoke_empty_response_payload(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    mock_response = {"Payload": MagicMock()}
    mock_response["Payload"].read.return_value = b""
    client.invoke.return_value = mock_response
    lambda_function_name = "my-lambda-function"

    response = invoke_function(lambda_function_name, invocation_type="Event")

    assert response["Payload"] == ""
    client.invoke.assert_called_with(
        FunctionName=lambda_function_name,
        InvocationType="Event",
        LogType="None",
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_put_function_timeout(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    timeout = 3
    put_function_timeout(lambda_function_name, timeout)
    client.update_function_configuration.assert_called_with(
        FunctionName=lambda_function_name, Timeout=timeout
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_put_function_memory_size(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    lambda_function_name = "my-lambda-function"
    memory_size = 512
    put_function_memory_size(lambda_function_name, memory_size)
    client.update_function_configuration.assert_called_with(
        FunctionName=lambda_function_name, MemorySize=memory_size
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_delete_event_source_mapping(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.delete_event_source_mapping.return_value = read_in_test_data(
        "delete_event_source_mapping.json"
    )
    uuid = "6b08c7db-a0f5-404d-ae73-b116d9125b0e"
    response = delete_event_source_mapping(event_uuid=uuid)
    assert response["State"] == "Deleting"
    client.delete_event_source_mapping.assert_called_with(UUID=uuid)


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_delete_event_source_mapping_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.delete_event_source_mapping.side_effect = mock_client_error(
        "delete_event_source_mapping"
    )

    with pytest.raises(FailedActivity) as x:
        uuid = "6b08c7db-a0f5-404d-ae73-b116d9125b0e"
        delete_event_source_mapping(event_uuid=uuid)
    assert "Test Error" in str(x)


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_toggle_event_source_mapping_enable(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.update_event_source_mapping.return_value = read_in_test_data(
        "update_event_source_mapping_enable.json"
    )
    uuid = "6b08c7db-a0f5-404d-ae73-b116d9125b0e"
    response = toggle_event_source_mapping_state(event_uuid=uuid, enabled=True)
    assert response["State"] == "Enabling"
    client.update_event_source_mapping.assert_called_with(
        UUID=uuid, Enabled=True
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_toggle_event_source_mapping_disable(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.update_event_source_mapping.return_value = read_in_test_data(
        "update_event_source_mapping_disable.json"
    )
    uuid = "6b08c7db-a0f5-404d-ae73-b116d9125b0e"
    response = toggle_event_source_mapping_state(event_uuid=uuid, enabled=False)
    assert response["State"] == "Disabling"
    client.update_event_source_mapping.assert_called_with(
        UUID=uuid, Enabled=False
    )


@patch("chaosaws.awslambda.actions.aws_client", autospec=True)
def test_aws_lambda_toggle_event_source_mapping_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.update_event_source_mapping.side_effect = mock_client_error(
        "update_event_source_mapping"
    )

    with pytest.raises(FailedActivity) as x:
        uuid = "6b08c7db-a0f5-404d-ae73-b116d9125b0e"
        toggle_event_source_mapping_state(uuid, False)
    assert "Test Error" in str(x)
