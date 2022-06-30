from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import ActivityFailed

from chaosaws.ssm.actions import (
    create_document,
    delete_document,
    put_parameter,
    send_command,
)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_create_documente_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name = ""
    content = ""
    with pytest.raises(ActivityFailed):
        create_document(path_content=content, name=name)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_send_command_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    document_name = ""
    with pytest.raises(ActivityFailed):
        send_command(document_name=document_name)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_send_command(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    document_name = "some_document_name"
    send_command(
        document_name=document_name,
        document_version="some_Document_version",
        max_concurrency="1",
        max_errors="2",
        parameters={"value": "some_value"},
        region="some_region",
        timeout_seconds=5,
        targets=[{"key": "value"}],
    )
    client.send_command.assert_called_with(
        DocumentName=document_name,
        DocumentVersion="some_Document_version",
        MaxConcurrency="1",
        MaxErrors="2",
        Parameters={"value": "some_value"},
        Targets=[{"key": "value"}],
        TimeoutSeconds=5,
    )


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_delete_document_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name = ""
    with pytest.raises(ActivityFailed):
        delete_document(name=name)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_delete_document(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name = "some_name"
    delete_document(name=name, version_name="some_version", force="some_force")
    client.delete_document.assert_called_with(
        Force="some_force", Name="some_name", VersionName="some_version"
    )


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_put_parameter_with_name_empty(aws_client: MagicMock) -> None:
    client = MagicMock()
    aws_client.return_value = client
    name = ""
    value = "value"
    with pytest.raises(ActivityFailed):
        put_parameter(name=name, value=value)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_put_parameter_with_value_empty(aws_client: MagicMock) -> None:
    client = MagicMock()
    aws_client.return_value = client
    name = "name"
    value = ""
    with pytest.raises(ActivityFailed):
        put_parameter(name=name, value=value)


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_put_parameter(aws_client: MagicMock) -> None:
    client = MagicMock()
    aws_client.return_value = client
    name = "name"
    value = "value"
    description = "some description"
    type = "SecureString"
    overwrite = True
    allowed_pattern = "pattern"
    tags = [{"name": "value"}]
    tier = "tier"
    policies = "policies"
    data_type = "dataType"
    put_parameter(
        name=name,
        value=value,
        description=description,
        type=type,
        overwrite=overwrite,
        allowed_pattern=allowed_pattern,
        tags=tags,
        tier=tier,
        policies=policies,
        data_type=data_type,
    )
    client.put_parameter.assert_called_with(
        AllowedPattern=allowed_pattern,
        DataType=data_type,
        Description=description,
        KeyId=None,
        Name=name,
        Overwrite=overwrite,
        Policies=policies,
        Tags=tags,
        Tier=tier,
        Type=type,
        Value=value,
    )


@patch("chaosaws.ssm.actions.aws_client", autospec=True)
def test_put_parameter_required(aws_client: MagicMock) -> None:
    client = MagicMock()
    aws_client.return_value = client
    name = "name"
    value = "value"
    put_parameter(
        name=name,
        value=value,
    )
    client.put_parameter.assert_called_with(
        AllowedPattern=None,
        DataType=None,
        Description=None,
        KeyId=None,
        Name=name,
        Overwrite=False,
        Policies=None,
        Tags=None,
        Tier=None,
        Type=None,
        Value=value,
    )
