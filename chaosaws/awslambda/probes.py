# -*- coding: utf-8 -*-
import boto3
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["get_function_concurrency", "get_function_timeout",
           "get_function_memory_size"]


def get_function_concurrency(function_name: str, configuration:
                             Configuration = None,
                             secrets: Secrets = None) -> bool:
    """
    Get configuration information of lambda by its function name
    """
    client = aws_client("lambda", configuration, secrets)
    result = client.get_function(FunctionName=function_name)
    return result["Concurrency"]["ReservedConcurrentExecutions"]


def get_function_timeout(function_name: str,
                         qualifier: str = None,
                         configuration: Configuration = None,
                         secrets: Secrets = None) -> int:
    """
    Get the configured timeout of a lambda function.

    The returned timeout is specified in number of seconds.
    """
    client = aws_client("lambda", configuration, secrets)
    function_configuration = _get_function_configuration(function_name, client,
                                                         qualifier)
    return function_configuration.get('Timeout')


def get_function_memory_size(function_name: str,
                             qualifier: str = None,
                             configuration: Configuration = None,
                             secrets: Secrets = None) -> int:
    """
    Get the configured memory size of a lambda function.

    The returned memory size is specified in megabytes.
    """
    client = aws_client("lambda", configuration, secrets)
    function_configuration = _get_function_configuration(function_name, client,
                                                         qualifier)
    return function_configuration.get('MemorySize')


###############################################################################
# Private functions
###############################################################################
def _get_function_configuration(function_name: str,
                                client: boto3.client,
                                qualifier: str = None) -> AWSResponse:
    request_kwargs = {
        'FunctionName': function_name
    }
    if qualifier is not None:
        request_kwargs['Qualifier'] = qualifier
    return client.get_function_configuration(**request_kwargs)
