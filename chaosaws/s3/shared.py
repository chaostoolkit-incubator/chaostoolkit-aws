from typing import List

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.types import AWSResponse


def list_buckets(client: boto3.client) -> List[str]:
    """List S3 buckets

    :param client: boto3 client
    :return: List[str]
    """
    response = client.list_buckets()
    return [r["Name"] for r in response["Buckets"]]


def get_object(
    client: boto3.client, bucket_name: str, object_key: str, version_id: str = None
) -> AWSResponse:
    """Get an object in a S3 bucket

    :param client: boto3 client
    :param bucket_name: the S3 bucket name
    :param object_key: the path to the object
    :param version_id: the version id of the object (optional)
    :return: AWSResponse (Dict[str, Any])
    """
    params = {
        "Bucket": bucket_name,
        "Key": object_key,
        **({"VersionId": version_id} if version_id else {}),
    }

    try:
        return client.get_object(**params)
    except ClientError as e:
        response = e.response["Error"]
        raise FailedActivity(f"[{response['Code']}] {response['Message']}")


def validate_bucket_exists(client: boto3.client, bucket_name: str) -> bool:
    buckets = list_buckets(client)
    return bucket_name in buckets


def validate_object_exists(
    client: boto3.client, bucket_name: str, object_key: str, version_id: str = None
) -> bool:
    try:
        get_object(client, bucket_name, object_key, version_id)
        return True
    except FailedActivity:
        return False


def get_bucket_versioning(client: boto3.client, bucket_name: str) -> str:
    response = client.get_bucket_versioning(Bucket=bucket_name)
    return response.get("Status", "Suspended")
