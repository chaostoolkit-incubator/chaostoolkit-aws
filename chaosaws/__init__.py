import logging
import os
from datetime import datetime, timedelta, timezone
from importlib.metadata import version, PackageNotFoundError
from typing import Any, Dict, List, Optional, Union

import boto3
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from chaoslib import __version__ as ctklib_version
from chaoslib.discovery.discover import (
    discover_actions,
    discover_activities,
    discover_probes,
    initialize_discovery_result,
)
from chaoslib.exceptions import InterruptExecution
from chaoslib.types import (
    Configuration,
    DiscoveredActivities,
    Discovery,
    Secrets,
)

__all__ = ["__version__", "discover", "aws_client", "signed_api_call"]

try:
    __version__ = version("chaostoolkit-aws")
except PackageNotFoundError:
    __version__ = "unknown"


def get_logger() -> logging.Logger:
    """
    Return the right logger based on which version of the Chaos Toolkit
    is our runtime. Starting from Chaos Toookit 1.19, the logger is named
    `"chaostoolkit"` as we dropped logzero. Before that version, we assume
    logzero still.
    """
    logger_name = "logzero_default"

    try:
        ctk_version = version("chaostoolkit")
        major, minor, _ = ctk_version.split(".", 2)
        if int(major) >= 1 and int(minor) >= 19:
            logger_name = "chaostoolkit"
        else:
            major, minor, _ = ctklib_version.split(".", 2)
            if int(major) >= 1 and int(minor) >= 42:
                logger_name = "chaostoolkit"
    except Exception:
        pass

    return logging.getLogger(logger_name)


logger = get_logger()


def get_credentials(secrets: Secrets = None) -> Dict[str, str]:
    """
    Credentials may be provided via the secrets object. When they aren't,
    they will be loaded from the process environment (for instance, read from
    `~/.aws/credentials`).

    See: https://boto3.readthedocs.io/en/latest/guide/configuration.html#guide-configuration
    """  # noqa: E501
    creds = dict(
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
    )

    if secrets:
        creds["aws_access_key_id"] = secrets.get("aws_access_key_id")
        creds["aws_secret_access_key"] = secrets.get("aws_secret_access_key")
        creds["aws_session_token"] = secrets.get("aws_session_token")

    return creds


def aws_client(
    resource_name: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Create a boto3 client for the given resource.

    You may pass the `aws_region` key in the `configuration` object to
    be explicit about which region you want to use.

    You may pass `aws_profile_name` value to the `configuration` object so that
    we load the appropriate profile to converse with the AWS services. In that
    case, make sure your local `~/aws/credentials` config is properly setup, as
    per https://boto3.readthedocs.io/en/latest/guide/configuration.html#aws-config-file

    Also, if you want to assume a role, you should setup that file as per
    https://boto3.readthedocs.io/en/latest/guide/configuration.html#assume-role-provider
    as we do not read those settings from the `secrets` object.
    """  # noqa: E501
    configuration = configuration or {}
    aws_profile_name = configuration.get("aws_profile_name")
    aws_assume_role_arn = configuration.get("aws_assume_role_arn")
    params = get_credentials(secrets)

    region = configuration.get("aws_region")
    if not region:
        logger.debug(
            "The configuration key `aws_region` is not set, looking in the "
            "environment instead for `AWS_REGION` or `AWS_DEFAULT_REGION`"
        )
        region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION"))
        if not region:
            raise InterruptExecution("AWS requires a region to be set!")

    if region:
        logger.debug(f"Using AWS region '{region}'")
        params["region_name"] = region

    if boto3.DEFAULT_SESSION is None:
        # we must create our own session so that we can populate the profile
        # name when it is provided. Only create the default session once.
        boto3.setup_default_session(profile_name=aws_profile_name, **params)

    if not aws_assume_role_arn:
        logger.debug(
            "Client will be using profile '{}' from boto3 session".format(
                aws_profile_name or "default"
            )
        )
        return boto3.client(resource_name, **params)
    else:
        logger.debug(
            "Fetching credentials dynamically assuming role '{}'".format(
                aws_assume_role_arn
            )
        )

        aws_assume_role_session_name = configuration.get(
            "aws_assume_role_session_name"
        )
        if not aws_assume_role_session_name:
            aws_assume_role_session_name = "ChaosToolkit"
            logger.debug(
                "You are missing the `aws_assume_role_session_name` "
                "configuration key. A unique one was generated: '{}'".format(
                    aws_assume_role_session_name
                )
            )

        client = boto3.client("sts", **params)
        params = {
            "RoleArn": aws_assume_role_arn,
            "RoleSessionName": aws_assume_role_session_name,
        }
        response = client.assume_role(**params)
        creds = response["Credentials"]
        logger.debug(
            "Temporary credentials will expire on {}".format(
                creds["Expiration"].isoformat()
            )
        )

        params = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
        if region:
            params["region_name"] = region

        return boto3.client(resource_name, **params)


def signed_api_call(
    service: str,
    path: str = "/",
    method: str = "GET",
    configuration: Configuration = None,
    secrets: Secrets = None,
    params: Dict[str, Any] = None,
) -> requests.Response:
    """
    Perform an API call against an AWS service.

    This should only be used when boto does not already implement the service
    itself. See https://boto3.readthedocs.io/en/latest/reference/services/index.html

    for a list of supported services by boto. This function does not claim
    being generic enough to support the whole range of AWS API.

    The `configuration` object should look like this:

    ```json
    {
        "aws_region": "us-east-1",
        "aws_host": "amazonaws.com"
    }
    ```

    While both are optional, and default to the values shown in this snippet,
    you should make sure to be explicit about them to avoid confusion.

    The endpoint being called is built from the given `service` name, the
    given region and host as well as the `path` of the action being called on
    the service. By default, the call is made over `HTTPS` but this can be
    changed by setting `aws_endpoint_scheme` in the configuration dictionary.

    Pass any parameters of the API itself as part of the remaining `params`
    paramater is a dictionary. It should match the signature of the service
    you are trying to call and will be sent as a query-string when `method` is
    `"GET"` or `"DELETE"`, or as a JSON payload otherwise. Refer to the AWS
    documentation for each service type.

    This function does not support profile names so you must provide the
    credentials in secrets.
    """  # noqa: E501
    configuration = configuration or {}
    region = configuration.get("aws_region", "us-east-1") or ""
    host = configuration.get("aws_host", "amazonaws.com")
    scheme = configuration.get("aws_endpoint_scheme", "https")
    host = f"{service}.{region}.{host}"
    endpoint = configuration.get("aws_endpoint", f"{scheme}://{host}").replace(
        "..", "."
    )
    endpoint = f"{endpoint}{path}"
    creds = get_credentials(secrets)

    # when creds weren't provided via secrets, we let boto search for them
    # from the process environment

    if creds["aws_access_key_id"] and creds["aws_secret_access_key"]:
        auth = AWSRequestsAuth(
            aws_access_key=creds["aws_access_key_id"],
            aws_secret_access_key=creds["aws_secret_access_key"],
            aws_host=host,
            aws_region=region,
            aws_service=service,
        )
    else:
        auth = BotoAWSRequestsAuth(
            aws_host=host, aws_region=region, aws_service=service
        )

    headers = {"Accept": "application/json"}

    if method in ("DELETE", "GET"):
        return requests.request(
            method, endpoint, headers=headers, auth=auth, params=params
        )

    return requests.request(
        method, endpoint, headers=headers, auth=auth, json=params
    )


def discover(discover_system: bool = True) -> Discovery:
    """
    Discover AWS capabilities from this extension as well, if a aws
    configuration is available, some information about the AWS environment.
    """
    logger.info("Discovering capabilities from chaostoolkit-aws")

    discovery = initialize_discovery_result(
        "chaostoolkit-aws", __version__, "aws"
    )
    discovery["activities"].extend(load_exported_activities())

    return discovery


###############################################################################
# Private functions
###############################################################################
def load_exported_activities() -> List[DiscoveredActivities]:
    """
    Extract metadata from actions and probes exposed by this extension.
    """
    activities = []
    activities.extend(discover_actions("chaosaws.ec2.actions"))
    activities.extend(discover_probes("chaosaws.ec2.probes"))
    activities.extend(discover_actions("chaosaws.ecs.actions"))
    activities.extend(discover_probes("chaosaws.ecs.probes"))
    activities.extend(discover_actions("chaosaws.iam.actions"))
    activities.extend(discover_probes("chaosaws.iam.probes"))
    activities.extend(discover_actions("chaosaws.eks.actions"))
    activities.extend(discover_probes("chaosaws.eks.probes"))
    activities.extend(discover_actions("chaosaws.elbv2.actions"))
    activities.extend(discover_probes("chaosaws.elbv2.probes"))
    activities.extend(discover_actions("chaosaws.asg.actions"))
    activities.extend(discover_probes("chaosaws.asg.probes"))
    activities.extend(discover_actions("chaosaws.awslambda.actions"))
    activities.extend(discover_probes("chaosaws.awslambda.probes"))
    activities.extend(discover_actions("chaosaws.cloudwatch.actions"))
    activities.extend(discover_probes("chaosaws.cloudwatch.probes"))
    activities.extend(discover_actions("chaosaws.rds.actions"))
    activities.extend(discover_probes("chaosaws.rds.probes"))
    activities.extend(discover_actions("chaosaws.elasticache.actions"))
    activities.extend(discover_probes("chaosaws.elasticache.probes"))
    activities.extend(discover_actions("chaosaws.emr.actions"))
    activities.extend(discover_probes("chaosaws.emr.probes"))
    activities.extend(discover_actions("chaosaws.route53.actions"))
    activities.extend(discover_probes("chaosaws.route53.probes"))
    activities.extend(discover_actions("chaosaws.ssm.actions"))
    activities.extend(discover_actions("chaosaws.fis.actions"))
    activities.extend(discover_probes("chaosaws.s3.probes"))
    activities.extend(discover_actions("chaosaws.s3.actions"))
    activities.extend(discover_probes("chaosaws.msk.probes"))
    activities.extend(discover_actions("chaosaws.msk.actions"))
    activities.extend(
        discover_activities("chaosaws.s3.controls.upload", "control")
    )
    activities.extend(discover_probes("chaosaws.xray.probes"))
    activities.extend(discover_probes("chaosaws.incidents.probes"))
    return activities


def time_to_datetime(
    ts: Union[str, float], offset: Optional[datetime] = None
) -> datetime:
    if isinstance(ts, float):
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if ts == "now":
        return datetime.now().astimezone(tz=timezone.utc)

    offset = offset or datetime.now().astimezone(tz=timezone.utc)
    quantity, unit = ts.split(" ", 1)
    duration = float(quantity)

    if unit in ("second", "seconds"):
        delta = 1
    elif unit in ("minute", "minutes"):
        delta = 60
    elif unit in ("hour", "hours"):
        delta = 60 * 60
    elif unit in ("day", "days"):
        delta = 60 * 60 * 24
    elif unit in ("month", "months"):
        delta = 60 * 60 * 24 * 30
    elif unit in ("year", "years"):
        delta = 60 * 60 * 24 * 365
    else:
        # let's default to the last 5mn
        delta = 300

    return offset - timedelta(seconds=duration * delta)


def convert_tags(tags: Union[str, Dict[str, str], None]) -> Dict[str, str]:
    """
    Convert a `k=v,x=y` string into a dictionary
    """
    if not tags:
        return {}

    if isinstance(tags, dict):
        return tags

    result = {}
    for t in tags.split(","):
        k, v = t.split("=", 1)
        result[k] = v

    return result


def tags_as_key_value_pairs(tags: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"Key": k, "Value": v} for k, v in tags.items()]
