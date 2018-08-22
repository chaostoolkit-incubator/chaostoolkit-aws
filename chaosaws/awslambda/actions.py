# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["put_function_concurrency", "delete_function_concurrency"]


def put_function_concurrency(function_name: str,
                             concurrent_executions: int,
                             configuration: Configuration = None,
                             secrets: Secrets = None) -> AWSResponse:
    """
    Throttles Lambda by setting reserved concurrency amount.
    """
    client = aws_client("lambda", configuration, secrets)
    if not function_name:
        raise FailedActivity(
            "you must specify the lambda function name"
        )
    try:
        return client.put_function_concurrency(
            FunctionName=function_name,
            ReservedConcurrentExecutions=concurrent_executions
        )
    except Exception as x:
        raise FailedActivity(
            "failed throttling lambda function '{}': '{}'".format(
                function_name, str(x)))


def delete_function_concurrency(function_name: str,
                                configuration: Configuration = None,
                                secrets: Secrets = None) -> AWSResponse:
    """
    Removes concurrency limit applied to the specified Lambda
    """
    client = aws_client("lambda", configuration, secrets)
    return client.delete_function_concurrency(FunctionName=function_name)
