# -*- coding: utf-8 -*-
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.s3.actions import delete_object, toggle_versioning

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def read_configs(filename):
    config = os.path.join(data_path, filename)
    with open(config, 'r') as fh:
        return json.loads(fh.read())


def mock_client_error(*args, **kwargs):
    return ClientError(
        operation_name=kwargs['op'],
        error_response={'Error': {
            'Code': kwargs['Code'],
            'Message': kwargs['Message']
        }}
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_delete_object_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_object.return_value = read_configs('get_object_1.json')
    client.delete_object.return_value = {}

    delete_object(
        bucket_name='Test-Bucket-1', object_key='path/to/some/file.json')

    client.delete_object.assert_called_with(
        Bucket='Test-Bucket-1', Key='path/to/some/file.json')


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_delete_object_false_invalid_bucket(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_object.return_value = read_configs('get_object_1.json')
    client.delete_object.return_value = {}

    with pytest.raises(FailedActivity) as x:
        delete_object(
            bucket_name='Test-Bucket-99', object_key='path/to/some/file.json')

    assert 'Bucket "Test-Bucket-99" does not exist!' in str(x)


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_delete_object_false_invalid_object(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_object.side_effect = mock_client_error(
        op='GetObject',
        Code='NoSuchKey',
        Message='The specified key does not exist.')
    client.delete_object.return_value = {}

    with pytest.raises(FailedActivity) as x:
        delete_object(
            bucket_name='Test-Bucket-1', object_key='path/to/some/invalid.json')

    assert 'Object "s3://Test-Bucket-1/path/to/some/invalid.json" ' \
           'does not exist!' in str(x)
    client.get_object.assert_called_with(
        Bucket='Test-Bucket-1',
        Key='path/to/some/invalid.json')


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_delete_object_version_true(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_object.return_value = read_configs('get_object_1.json')
    client.delete_object.return_value = {}

    delete_object(
        bucket_name='Test-Bucket-1',
        object_key='path/to/some/file.json',
        version_id='ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi'
    )

    client.delete_object.assert_called_with(
        Bucket='Test-Bucket-1',
        Key='path/to/some/file.json',
        VersionId='ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi'
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_delete_object_version_false_invalid_version(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_object.side_effect = mock_client_error(
        op='GetObject',
        Code='InvalidArgument',
        Message='Invalid version id specified')

    with pytest.raises(FailedActivity) as x:
        delete_object(
            bucket_name='Test-Bucket-1',
            object_key='path/to/some/file.json',
            version_id='de_zrueYdh.aBcdEfGhi'
        )

    assert 'Object "s3://Test-Bucket-1/path/to/some/file.json[' \
           'de_zrueYdh.aBcdEfGhi]" does not exist!' in str(x)
    client.get_object.assert_called_with(
        Bucket='Test-Bucket-1',
        Key='path/to/some/file.json',
        VersionId='de_zrueYdh.aBcdEfGhi'
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_no_bucket(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_1.json')

    params = {"bucket_name": "Test-Bucket-15", "status": "Enabled"}

    with pytest.raises(FailedActivity) as x:
        toggle_versioning(**params)
    assert "Bucket \"Test-Bucket-15\" does not exist!" in str(x)


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_enable(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_1.json')

    params = {"bucket_name": "Test-Bucket-8", "status": "Enabled"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8",
        VersioningConfiguration={
            "Status": "Enabled"
        }
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_enable_exception(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_2.json')

    params = {"bucket_name": "Test-Bucket-8", "status": "Enabled"}

    with pytest.raises(FailedActivity) as x:
        toggle_versioning(**params)

    assert "Bucket Test-Bucket-8 versioning is already Enabled!" in str(x)


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_enable_auto(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_1.json')

    params = {"bucket_name": "Test-Bucket-8"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8",
        VersioningConfiguration={
            "Status": "Enabled"
        }
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_suspend(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_2.json')

    params = {"bucket_name": "Test-Bucket-8", "status": "Suspended"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8",
        VersioningConfiguration={
            "Status": "Suspended"
        }
    )


@patch('chaosaws.s3.actions.aws_client', autospec=True)
def test_toggle_versioning_suspend_auto(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.list_buckets.return_value = read_configs('list_buckets_1.json')
    client.get_bucket_versioning.return_value = read_configs(
        'get_bucket_versioning_2.json')

    params = {"bucket_name": "Test-Bucket-8"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8",
        VersioningConfiguration={
            "Status": "Suspended"
        }
    )