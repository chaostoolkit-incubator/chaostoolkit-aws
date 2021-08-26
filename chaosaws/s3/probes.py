# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.s3.shared import validate_bucket_exists, validate_object_exists

__all__ = ['bucket_exists', 'object_exists']


def bucket_exists(bucket_name: str,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> bool:
    """Validate that a bucket exists

    :param bucket_name: The name of the S3 bucket
    :param configuration: access values used by actions/probes
    :param secrets: values that need to be passed on to actions/probes
    :return: boolean
    """
    client = aws_client('s3', configuration, secrets)
    return validate_bucket_exists(client, bucket_name)


def object_exists(bucket_name: str,
                  object_key: str,
                  version_id: str = None,
                  configuration: Configuration = None,
                  secrets: Secrets = None) -> bool:
    """Validate that an object exists in a S3 bucket

    :param bucket_name: the name of the S3 bucket
    :param object_key: the path to the object
    :param version_id: the version id of the object (optional)
    :param configuration: access values used by actions/probes (optional)
    :param secrets: values that need to be passed on to actions/probes (optional)
    :return: boolean
    """  # noqa: E501
    client = aws_client('s3', configuration, secrets)
    if not validate_bucket_exists(client, bucket_name):
        raise FailedActivity('Bucket "%s" does not exist!' % bucket_name)
    return validate_object_exists(client, bucket_name, object_key, version_id)

