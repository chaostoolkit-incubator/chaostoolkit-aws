import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws import aws_client
from chaosaws.s3.probes import bucket_exists, object_exists, versioning_status

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


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_bucket_exists_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")

    response = bucket_exists("Test-Bucket-7")
    assert response


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_bucket_exists_false(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")

    response = bucket_exists("Test-Bucket-99")
    assert not response


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_object_exists_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.return_value = read_configs("get_object_1.json")

    response = object_exists(
        bucket_name="Test-Bucket-1",
        object_key="another/random/path/to/file.json",
    )

    assert response
    client.get_object.assert_called_with(
        Bucket="Test-Bucket-1", Key="another/random/path/to/file.json"
    )


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_object_exists_false(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.side_effect = mock_client_error(
        op="GetObject",
        Code="NoSuchKey",
        Message="The specified key does not exist.",
    )

    response = object_exists(
        bucket_name="Test-Bucket-1",
        object_key="another/random/path/to/invalid.json",
    )

    assert not response
    client.get_object.assert_called_with(
        Bucket="Test-Bucket-1", Key="another/random/path/to/invalid.json"
    )


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_object_exists_invalid_bucket(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")

    with pytest.raises(FailedActivity) as x:
        object_exists(
            bucket_name="Test-Bucket-99",
            object_key="another/random/path/to/file.json",
        )

    assert 'Bucket "Test-Bucket-99" does not exist!' in str(x)


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_object_version_exists_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.return_value = read_configs("get_object_1.json")

    response = object_exists(
        bucket_name="Test-Bucket-1",
        object_key="another/random/path/to/file.json",
        version_id="ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi",
    )

    assert response
    client.get_object.assert_called_with(
        Bucket="Test-Bucket-1",
        Key="another/random/path/to/file.json",
        VersionId="ab_cDefGhiJklMnoPqRsTu.aBcdEfGhi",
    )


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_object_version_exists_false(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_object.side_effect = mock_client_error(
        op="GetObject",
        Code="InvalidArgument",
        Message="Invalid version id specified",
    )

    response = object_exists(
        bucket_name="Test-Bucket-1",
        object_key="another/random/path/to/file.json",
        version_id="qa_irdksL.jgfiw",
    )

    assert not response
    client.get_object.assert_called_with(
        Bucket="Test-Bucket-1",
        Key="another/random/path/to/file.json",
        VersionId="qa_irdksL.jgfiw",
    )


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_bucket_versioning_suspended_true(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_1.json"
    )

    response = versioning_status(
        bucket_name="Test-Bucket-1", status="Suspended"
    )
    assert response


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_bucket_versioning_suspended_false(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")
    client.get_bucket_versioning.return_value = read_configs(
        "get_bucket_versioning_1.json"
    )

    response = versioning_status(bucket_name="Test-Bucket-1", status="Enabled")
    assert not response


def test_bucket_versioning_invalid_status():
    with pytest.raises(FailedActivity) as x:
        versioning_status(bucket_name="Test-Bucket-1", status="Disabled")
    assert '"status" not one of "Enabled" or "Suspended"' in str(x)


@patch("chaosaws.s3.probes.aws_client", autospec=True)
def test_bucket_versioning_invalid_bucket(test_client: aws_client):
    client = MagicMock()
    test_client.return_value = client
    client.list_buckets.return_value = read_configs("list_buckets_1.json")

    with pytest.raises(FailedActivity) as x:
        versioning_status(bucket_name="Test-Bucket-99", status="Enabled")
    assert 'Bucket "Test-Bucket-99" does not exist!' in str(x)
