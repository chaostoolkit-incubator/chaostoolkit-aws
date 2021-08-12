import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "get_function_concurrency",
    "get_function_timeout",
    "get_function_memory_size",
    "list_event_source_mapping",
]


def get_function_concurrency(
    function_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> bool:
    """
    Get configuration information of lambda by its function name
    """
    client = aws_client("lambda", configuration, secrets)
    result = client.get_function(FunctionName=function_name)
    return result["Concurrency"]["ReservedConcurrentExecutions"]


def get_function_timeout(
    function_name: str,
    qualifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """
    Get the configured timeout of a lambda function.

    The returned timeout is specified in number of seconds.
    """
    client = aws_client("lambda", configuration, secrets)
    function_configuration = _get_function_configuration(
        function_name, client, qualifier
    )
    return function_configuration.get("Timeout")


def get_function_memory_size(
    function_name: str,
    qualifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> int:
    """
    Get the configured memory size of a lambda function.

    The returned memory size is specified in megabytes.
    """
    client = aws_client("lambda", configuration, secrets)
    function_configuration = _get_function_configuration(
        function_name, client, qualifier
    )
    return function_configuration.get("MemorySize")


def list_event_source_mapping(
    source_arn: str = None,
    function_name: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    List event source mappings for the provided lambda function or ARN of the
    event source

    :param source_arn: The ARN of the event source
    :param function_name: The name of the lambda function
    :param configuration: AWS configuration data
    :param secrets: AWS secrets
    :return: AWSResponse
    """
    if not any([source_arn, function_name]):
        raise FailedActivity(
            'must specify at least one of "source_arn" or "function_name"'
        )

    client = aws_client("lambda", configuration, secrets)

    params = {
        **({"EventSourceArn": source_arn} if source_arn else {}),
        **({"FunctionName": function_name} if function_name else {}),
    }

    try:
        return client.list_event_source_mappings(**params)
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])


###############################################################################
# Private functions
###############################################################################
def _get_function_configuration(
    function_name: str, client: boto3.client, qualifier: str = None
) -> AWSResponse:
    request_kwargs = {"FunctionName": function_name}
    if qualifier is not None:
        request_kwargs["Qualifier"] = qualifier
    return client.get_function_configuration(**request_kwargs)
