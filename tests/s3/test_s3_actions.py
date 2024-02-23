import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws import aws_client
from chaosaws.s3.actions import delete_object, toggle_versioning

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_configs(filename: str) -> dict:
    config = os.path.join(data_path, filename)
    with open(config, "r") as fh:
        return json.loads(fh.read())


def mock_client_error(*args, **kwargs) -> ClientError:
    return ClientError(
        operation_name=kwargs["op"],
        error_response={
            "Error": {"Code": kwargs["Code"], "Message": kwargs["Message"]}
        },
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_delete_object_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.return_value = read_configs("get_object_1.json")
    client.delete_object.return_value = {}

    delete_object(
        bucket_name="Test-Bucket-1", object_key="path/to/some/file.json"
    )

    client.delete_object.assert_called_with(
        Bucket="Test-Bucket-1", Key="path/to/some/file.json"
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_delete_object_false_invalid_bucket(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.return_value = read_configs("get_object_1.json")
    client.delete_object.return_value = {}

    with pytest.raises(FailedActivity) as x:
        delete_object(
            bucket_name="Test-Bucket-99", object_key="path/to/some/file.json"
        )

    assert 'Bucket "Test-Bucket-99" does not exist!' in str(x)


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_delete_object_version_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.return_value = read_configs("get_object_1.json")
    client.delete_object.return_value = {}

    delete_object(
        bucket_name="Test-Bucket-1",
        object_key="path/to/some/file.json",
        version_id="ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi",
    )

    client.delete_object.assert_called_with(
        Bucket="Test-Bucket-1",
        Key="path/to/some/file.json",
        VersionId="ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi",
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_toggle_versioning_no_bucket(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_1.json"
    )

    params = {"bucket_name": "Test-Bucket-15", "status": "Enabled"}

    with pytest.raises(FailedActivity) as x:
        toggle_versioning(**params)
    assert 'Bucket "Test-Bucket-15" does not exist!' in str(x)


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_toggle_versioning_enable(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_1.json"
    )

    params = {"bucket_name": "Test-Bucket-8", "status": "Enabled"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8", VersioningConfiguration={"Status": "Enabled"}
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_toggle_versioning_enable_auto(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_1.json"
    )

    params = {"bucket_name": "Test-Bucket-8"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8", VersioningConfiguration={"Status": "Enabled"}
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_toggle_versioning_suspend(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_2.json"
    )

    params = {"bucket_name": "Test-Bucket-8", "status": "Suspended"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8", VersioningConfiguration={"Status": "Suspended"}
    )


@patch("chaosaws.s3.actions.aws_client", autospec=True)
def test_toggle_versioning_suspend_auto(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_2.json"
    )

    params = {"bucket_name": "Test-Bucket-8"}
    toggle_versioning(**params)

    client.put_bucket_versioning.assert_called_with(
        Bucket="Test-Bucket-8", VersioningConfiguration={"Status": "Suspended"}
    )
