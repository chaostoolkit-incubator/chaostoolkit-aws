from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.s3.shared import get_bucket_versioning, validate_bucket_exists

__all__ = ["delete_object", "toggle_versioning"]


def delete_object(
    bucket_name: str,
    object_key: str,
    version_id: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """Delete an object in a S3 bucket

    :param bucket_name: the S3 bucket name
    :param object_key: the path to the object
    :param version_id: the version id of the object (optional)
    :param configuration: access values used by actions/probes (optional)
    :param secrets: values that need to be passed on to actions/probes (optional)
    :return: None
    """
    client = aws_client("s3", configuration, secrets)
    if not validate_bucket_exists(client, bucket_name):
        raise FailedActivity(f'Bucket "{bucket_name}" does not exist!')

    params = {
        "Bucket": bucket_name,
        "Key": object_key,
        **({"VersionId": version_id} if version_id else {}),
    }
    client.delete_object(**params)


def toggle_versioning(
    bucket_name: str,
    mfa_delete: str = None,
    status: str = None,
    mfa: str = None,
    owner: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> None:
    """Toggles versioning on a S3 bucket

    If the "status" parameter is not provided, the bucket will be scanned to
    determine if versioning is enabled. If it is enabled, it will be suspended.
    If it is suspended it will be enabled using basic values unless MFA is provided.

    :param bucket_name: The S3 bucket name
    :param status: "Enabled" to turn on versioning, "Suspended" to disable
    :param mfa: The authentication device serial number, a space, and the value from
        the device (optional)
    :param mfa_delete: Specifies if MFA delete is enabled in the bucket versioning
        (optional)
    :param owner: The account ID of the expected bucket owner (optional)
    :param configuration: access values used by actions/probes (optional)
    :param secrets: values that need to be passed on to actions/probes (optional)
    :return: None
    """
    client = aws_client("s3", configuration, secrets)
    if not validate_bucket_exists(client, bucket_name):
        raise FailedActivity(f'Bucket "{bucket_name}" does not exist!')

    versioning_status = get_bucket_versioning(client, bucket_name)
    if not status:
        status = "Suspended"
        if versioning_status == "Suspended":
            status = "Enabled"

    params = {
        "Bucket": bucket_name,
        **({"MFA": mfa} if mfa else {}),
        **({"ExpectedBucketOwner": owner} if owner else {}),
        "VersioningConfiguration": {
            "Status": status,
            **({"MFADelete": mfa_delete} if mfa_delete else {}),
        },
    }
    client.put_bucket_versioning(**params)
