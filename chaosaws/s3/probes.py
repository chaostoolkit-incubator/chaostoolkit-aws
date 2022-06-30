from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.s3.shared import (
    get_bucket_versioning,
    validate_bucket_exists,
    validate_object_exists,
)

__all__ = ["bucket_exists", "object_exists"]


def bucket_exists(
    bucket_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> bool:
    """Validate that a bucket exists

    :param bucket_name: The name of the S3 bucket
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: boolean
    """
    client = aws_client("s3", configuration, secrets)
    return validate_bucket_exists(client, bucket_name)


def object_exists(
    bucket_name: str,
    object_key: str,
    version_id: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """Validate that an object exists in a S3 bucket

    :param bucket_name: the name of the S3 bucket
    :param object_key: the path to the object
    :param version_id: the version id of the object (optional)
    :param configuration: access values used by actions/probes (optional)
    :param secrets: values that need to be passed on to actions/probes (optional)
    :return: boolean
    """
    client = aws_client("s3", configuration, secrets)
    if not validate_bucket_exists(client, bucket_name):
        raise FailedActivity(f'Bucket "{bucket_name}" does not exist!')
    return validate_object_exists(client, bucket_name, object_key, version_id)


def versioning_status(
    bucket_name: str,
    status: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    """
    Checks the versioning status of a bucket against the provided status

    :param bucket_name: the name of the S3 bucket
    :param status: either 'Enabled' or 'Suspended'
    :param configuration: access values used by actions/probes (optional)
    :param secrets: values that need to be passed on to actions/probes (optional)
    :return: boolean
    """
    if status not in ("Enabled", "Suspended"):
        raise FailedActivity('Parameter "status" not one of "Enabled" or "Suspended"')

    client = aws_client("s3", configuration, secrets)
    if not validate_bucket_exists(client, bucket_name):
        raise FailedActivity(f'Bucket "{bucket_name}" does not exist!')

    versioning = get_bucket_versioning(client, bucket_name)
    if versioning.lower() == status.lower():
        return True
    return False
