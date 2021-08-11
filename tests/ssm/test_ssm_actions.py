from unittest.mock import MagicMock, patch,mock_open
import os
import pytest
from chaoslib.exceptions import ActivityFailed
from chaosaws.ssm.actions import (create_document, send_command,
                                  delete_document)


@patch('chaosaws.ssm.actions.aws_client', autospec=True)
def test_create_documente_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name=''
    content=''
    with pytest.raises(ActivityFailed):
        create_document(path_content=content,name=name)


@patch('chaosaws.ssm.actions.aws_client', autospec=True)
def test_send_command_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    document_name=''
    with pytest.raises(ActivityFailed):
        send_command(document_name=document_name)

@patch('chaosaws.ssm.actions.aws_client', autospec=True)
def test_send_command(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    document_name='some_document_name'
    send_command(document_name=document_name,document_version='some_Document_version',max_concurrency="1",max_errors="2",parameters={'value':'some_value'},region='some_region')
    client.send_command(DocumentName=document_name,DocumentVersion='some_Document_version',MaxConcurrency="1",MaxErrors="2",Parameters=[{'value':'some_value'}],Region='some_region')


@patch('chaosaws.ssm.actions.aws_client', autospec=True)
def test_delete_document_with_params_required_empty(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name=''
    with pytest.raises(ActivityFailed):
        delete_document(name=name)

@patch('chaosaws.ssm.actions.aws_client', autospec=True)
def test_delete_document(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    name='some_name'
    delete_document(name=name,version_name='some_version',force='some_force')
    client.delete_document(Name=name,DocumentVersion='some_version',Force='some_force')

