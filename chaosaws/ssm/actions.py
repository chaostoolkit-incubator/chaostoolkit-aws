# -*- coding: utf-8 -*-
import random
import re
from typing import Any, Dict, List, Union

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["create_document","send_command","delete_document"]


def create_document(path_content: str = None, 
                    name: str = None,
                    version_name: str = None, 
                    document_type: str = None,
                    document_format: str = None,
                    configuration: Configuration = None,
                    secrets: Secrets = None) -> AWSResponse:
    """
    creates a Systems Manager (SSM) document.

    An SSM document defines the actions that Systems Manager performs on your managed instances. 
    For more information about SSM documents, including information about supported schemas, features, and syntax:
    https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-ssm-docs.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.create_document
    """

    if not any([path_content, name]):
        raise FailedActivity('To create a document, you must specify the  content and name')

    try:
        with open(path_content) as openFile:
            document_content = openFile.read()
            client = aws_client('ssm', configuration, secrets)
            return client.create_document(Content=document_content,Name=name,VersionName=version_name,DocumentType=document_type,DocumentFormat=document_format)
    except ClientError as e:
        raise FailedActivity('Failed to create document %s: %s' % (name, e.response['Error']['Message']))

def send_command (targets:List[Dict[str, Any]]=None,
                  document_name: str = None,
                  document_version: str = None,
                  parameters:Dict[str, Any]=None,
                  timeout_seconds: int = None,
                  max_concurrency: str = None,
                  max_errors: str = None,
                  region: str=None,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> AWSResponse:
    """
    Runs commands on one or more managed instances.

    An SSM document defines the actions that Systems Manager performs on your managed instances. 
    For more information about SSM SendCommand:
    https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_SendCommand.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.send_command
    """

    if not any([document_name]):
        raise FailedActivity('To run commands, you must specify the document_name')

    try:
        client = aws_client('ssm', configuration, secrets)
        return client.send_command(DocumentName=document_name,DocumentVersion=document_version,Targets=targets,TimeoutSeconds=timeout_seconds,Parameters=parameters,
                               MaxConcurrency=max_concurrency,MaxErrors=max_errors)
    except ClientError as e:
        raise FailedActivity('Failed to send command for document  %s: %s' % (document_name, e.response['Error']['Message']))

def delete_document(name: str = None,
                    version_name: str = None, 
                    force: bool=True,
                    configuration: Configuration = None,
                    secrets: Secrets = None) -> AWSResponse:
    """
    creates a Systems Manager (SSM) document.

    An SSM document defines the actions that Systems Manager performs on your managed instances. 
    For more information about SSM documents, including information about supported schemas, features, and syntax:
    https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-ssm-docs.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.create_document
    """

    if not any(name):
        raise FailedActivity('To create a document, you must specify the  name')

    try:
        client = aws_client('ssm', configuration, secrets)
        return client.delete_document(Name =name,VersionName=version_name,Force=force)
    except ClientError as e:
        raise FailedActivity('Failed to delete  document  %s: %s' % (name, e.response['Error']['Message']))