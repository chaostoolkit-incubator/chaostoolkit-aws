from typing import Any, Dict, List

from botocore.exceptions import ClientError
from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["create_document", "send_command", "delete_document", "put_parameter"]


def create_document(
    path_content: str,
    name: str,
    version_name: str = None,
    document_type: str = None,
    document_format: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    creates a Systems Manager (SSM) document.
    An SSM document defines the actions that SSM performs on your managed.
    For more information about SSM documents:
    https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-ssm-docs.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.create_document
    """

    if not any([path_content, name]):
        raise ActivityFailed(
            "To create a document," "you must specify the  content and name"
        )

    try:
        with open(path_content) as open_file:
            document_content = open_file.read()
            client = aws_client("ssm", configuration, secrets)
            return client.create_document(
                Content=document_content,
                Name=name,
                VersionName=version_name,
                DocumentType=document_type,
                DocumentFormat=document_format,
            )
    except ClientError as e:
        raise ActivityFailed(
            "Failed to create document '{}': '{}'".format(
                name, str(e.response["Error"]["Message"])
            )
        )


def send_command(
    document_name: str,
    targets: List[Dict[str, Any]] = None,
    document_version: str = None,
    parameters: Dict[str, Any] = None,
    timeout_seconds: int = None,
    max_concurrency: str = None,
    max_errors: str = None,
    region: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Runs commands on one or more managed instances.

    An SSM document defines the actions that SSM performs on your managed.
    For more information about SSM SendCommand:
    https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_SendCommand.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.send_command
    """

    if not any([document_name]):
        raise ActivityFailed("To run commands," "you must specify the document_name")

    try:
        client = aws_client("ssm", configuration, secrets)
        return client.send_command(
            DocumentName=document_name,
            DocumentVersion=document_version,
            Targets=targets,
            TimeoutSeconds=timeout_seconds,
            Parameters=parameters,
            MaxConcurrency=max_concurrency,
            MaxErrors=max_errors,
        )
    except ClientError as e:
        raise ActivityFailed(
            "Failed to send command for document  '{}': '{}'".format(
                document_name, str(e.response["Error"]["Message"])
            )
        )


def delete_document(
    name: str,
    version_name: str = None,
    force: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    creates a Systems Manager (SSM) document.

    An SSM document defines the actions that SSM performs on your managed.
    For more information about SSM documents:
    https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-ssm-docs.html
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.create_document
    """

    if not any(name):
        raise ActivityFailed("To create a document," "you must specify the  name")

    try:
        client = aws_client("ssm", configuration, secrets)
        kwargs = {"Name": name, "Force": force}
        if version_name:
            kwargs["VersionName"] = version_name
        return client.delete_document(**kwargs)
    except ClientError as e:
        raise ActivityFailed(
            "Failed to delete  document '{}': '{}'".format(
                name, str(e.response["Error"]["Message"])
            )
        )


def put_parameter(
    name: str,
    value: str,
    description: str = None,
    type: str = None,
    key_id: str = None,
    overwrite: bool = False,
    allowed_pattern: str = None,
    tags: List[Dict[str, str]] = None,
    tier: str = None,
    policies: str = None,
    data_type: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Add or update a parameter in the Systems Manager Parameter Store.

    :param name: str name of the parameter
    :param value: str value of the parameter
    :param description: str information about the parameter
    :param type: str type of the paramater value, such as 'String'
    :param key_id: str KMS key id to use while encrypting the parameter value
    :param overwrite: bool allow the parameter value to be overwritten
    :param allowed_pattern: str regex to validate parameter value
    :param tags: List[Dict[str, str]] metadata about the parameter
    :param tier: str storage classes such as 'Advanced' to allow larger parameter
        values
    :param policies: str storage policies such as expiration in JSON format
    :param data_type: str data type for String. Allows the validation of AMI IDs
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: dict representing the Version and Tier of the parameter

    Examples
    --------
    >>> Configuration within experiment
       {
            "name": "Activate Chaos",
            "type": "action",
            "provider": {
                "type": "python",
                "module": "chaosaws.ssm.actions",
                "func": "put_parameter",
                "arguments": {
                    "name": "chaos_trigger",
                    "value": true,
                    "overwrite": true,
                    "type": "SecureString",
                }
            },
        }

    """
    if not name:
        raise ActivityFailed("To create a parameter, you must specify the name")

    if not value:
        raise ActivityFailed("To create a parameter, you must specify the value")

    try:
        client = aws_client("ssm", configuration, secrets)
        kwargs = {
            "Name": name,
            "Description": description,
            "Value": value,
            "Type": type,
            "KeyId": key_id,
            "Overwrite": overwrite,
            "AllowedPattern": allowed_pattern,
            "Tags": tags,
            "Tier": tier,
            "Policies": policies,
            "DataType": data_type,
        }
        return client.put_parameter(**kwargs)
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        raise ActivityFailed(f"Failed to put  parameter '{name}': '{error_message}'")
