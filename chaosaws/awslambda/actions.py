import json
from base64 import b64encode
from json.decoder import JSONDecodeError
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "invoke_function",
    "put_function_concurrency",
    "delete_function_concurrency",
    "put_function_timeout",
    "put_function_memory_size",
    "delete_event_source_mapping",
    "toggle_event_source_mapping_state",
]


def invoke_function(
    function_name: str,
    function_arguments: Dict[str, Any] = None,
    invocation_type: str = "RequestResponse",
    client_context: Dict[str, Any] = None,
    qualifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Invokes Lambda.

    More information about request arguments are available in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.invoke
    """  # noqa: E501
    client = aws_client("lambda", configuration, secrets)
    request_kwargs = {
        "FunctionName": function_name,
        "InvocationType": invocation_type,
        "LogType": "None",
    }
    if function_arguments is not None:
        request_kwargs["Payload"] = json.dumps(function_arguments)
    if client_context is not None:
        client_context_jsonbytes = json.dumps(client_context).encode()
        client_context_b64str = b64encode(client_context_jsonbytes).decode()
        request_kwargs["ClientContext"] = client_context_b64str
    if qualifier is not None:
        request_kwargs["Qualifier"] = qualifier
    try:
        response = client.invoke(**request_kwargs)
    except Exception as x:
        raise FailedActivity(f"failed invoking function '{function_name}': '{str(x)}'")
    if "Payload" in response:
        # The payload is of type StreamingBody and
        # cannot be directly serialized into JSON
        response_payload = response["Payload"].read().decode()
        response.pop("Payload", None)
        try:
            response["Payload"] = json.loads(response_payload)
        except JSONDecodeError:
            response["Payload"] = response_payload
    return response


def put_function_concurrency(
    function_name: str,
    concurrent_executions: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Throttles Lambda by setting reserved concurrency amount.
    """
    client = aws_client("lambda", configuration, secrets)
    if not function_name:
        raise FailedActivity("you must specify the lambda function name")
    try:
        return client.put_function_concurrency(
            FunctionName=function_name,
            ReservedConcurrentExecutions=concurrent_executions,
        )
    except Exception as x:
        raise FailedActivity(
            f"failed throttling lambda function '{function_name}': '{str(x)}'"
        )


def delete_function_concurrency(
    function_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Removes concurrency limit applied to the specified Lambda
    """
    client = aws_client("lambda", configuration, secrets)
    return client.delete_function_concurrency(FunctionName=function_name)


def put_function_timeout(
    function_name: str,
    timeout: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Sets the function timeout.

    Input timeout argument is specified in seconds.
    """
    client = aws_client("lambda", configuration, secrets)
    return _update_function_configuration(
        function_name=function_name, client=client, timeout=timeout
    )


def put_function_memory_size(
    function_name: str,
    memory_size: int,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Sets the function memory size.

    Input memory_size argument is specified in megabytes.
    """
    client = aws_client("lambda", configuration, secrets)
    return _update_function_configuration(
        function_name=function_name, client=client, memory_size=memory_size
    )


def delete_event_source_mapping(
    event_uuid: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Delete an event source mapping

    :param event_uuid: The identifier of the event source mapping
    :param configuration: AWS configuration data
    :param secrets: AWS secrets
    :return: AWSResponse
    """
    client = aws_client("lambda", configuration, secrets)
    try:
        return client.delete_event_source_mapping(UUID=event_uuid)
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])


def toggle_event_source_mapping_state(
    event_uuid: str,
    enabled: bool,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Toggle an event source mapping to be disabled or enabled

    :param event_uuid: The identifier of the event source mapping
    :param enabled: Boolean value: true to enable, false to disable
    :param configuration: AWS configuration data
    :param secrets: AWS secrets
    :return: AWSResponse
    """
    client = aws_client("lambda", configuration, secrets)
    try:
        return client.update_event_source_mapping(UUID=event_uuid, Enabled=enabled)
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])


###############################################################################
# Private functions
###############################################################################
def _update_function_configuration(
    function_name: str,
    client: boto3.client,
    timeout: int = None,
    memory_size: int = None,
) -> AWSResponse:
    request_kwargs = {"FunctionName": function_name}
    if timeout is not None:
        request_kwargs["Timeout"] = timeout
    if memory_size is not None:
        request_kwargs["MemorySize"] = memory_size
    return client.update_function_configuration(**request_kwargs)
