# -*- coding: utf-8 -*-
from chaoslib.types import Configuration, Secrets
from chaosaws import aws_client

__all__ = ["get_function_concurrency"]


def get_function_concurrency(function_name: str, configuration:
                             Configuration = None,
                             secrets: Secrets = None) -> bool:
    """
    Get configuration information of lambda by its function name
    """
    client = aws_client("lambda", configuration, secrets)
    result = client.get_function(FunctionName=function_name)
    return result["Concurrency"]["ReservedConcurrentExecutions"]
