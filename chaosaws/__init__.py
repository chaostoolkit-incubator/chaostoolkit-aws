# -*- coding: utf-8 -*-
from typing import Any, Dict, List

import boto3
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from botocore import parsers
from chaosaws.types import AWSResponse
from chaoslib.discovery.discover import (discover_actions, discover_probes,
                                         initialize_discovery_result)
from chaoslib.exceptions import DiscoveryFailed
from chaoslib.types import (Configuration, DiscoveredActivities,
                            DiscoveredSystemInfo, Discovery, Secrets)
from logzero import logger

__version__ = '0.7.0'
__all__ = ["__version__", "discover", "aws_client", "signed_api_call"]


def get_credentials(secrets: Secrets = None) -> Dict[str, str]:
    """
    Credentialss may be provided via the secrets object. When they aren't,
    they will be loaded from the process environment (for instance, read from
    `~/.aws/credentials`).

    See: https://boto3.readthedocs.io/en/latest/guide/configuration.html#guide-configuration
    """  # noqa: E501
    creds = dict(
        aws_access_key_id=None, aws_secret_access_key=None,
        aws_session_token=None)

    if secrets:
        creds["aws_access_key_id"] = secrets.get("aws_access_key_id")
        creds["aws_secret_access_key"] = secrets.get("aws_secret_access_key")
        creds["aws_session_token"] = secrets.get("aws_session_token")

    return creds


def aws_client(resource_name: str, configuration: Configuration = None,
               secrets: Secrets = None):
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
    region = configuration.get("aws_region", "us-east-1")
    creds = get_credentials(secrets)

    if boto3.DEFAULT_SESSION is None:
        profile_name = configuration.get("aws_profile_name")

        # we must create our own session so that we can populate the profile
        # name when it is provided. Only create the default session once.
        boto3.setup_default_session(
            profile_name=profile_name, region_name=region, **creds)

    return boto3.client(resource_name, region_name=region, **creds)


def signed_api_call(service: str, path: str = "/", method: str = 'GET',
                    configuration: Configuration = None,
                    secrets: Secrets = None,
                    params: Dict[str, Any] = None) -> requests.Response:
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
    host = "{s}.{r}.{h}".format(s=service, r=region, h=host)
    endpoint = configuration.get(
        "aws_endpoint", '{scheme}://{h}'.format(
            scheme=scheme, h=host)).replace('..', '.')
    endpoint = "{e}{p}".format(e=endpoint, p=path)
    creds = get_credentials(secrets)

    # when creds weren't provided via secrets, we let boto search for them
    # from the process environment

    if creds["aws_access_key_id"] and creds["aws_secret_access_key"]:
        auth = AWSRequestsAuth(
            aws_access_key=creds["aws_access_key_id"],
            aws_secret_access_key=creds["aws_secret_access_key"],
            aws_host=host,
            aws_region=region,
            aws_service=service)
    else:
        auth = BotoAWSRequestsAuth(
            aws_host=host,
            aws_region=region,
            aws_service=service)

    headers = {
        "Accept": "application/json"
    }

    if method in ('DELETE', 'GET'):
        return requests.request(
            method, endpoint, headers=headers, auth=auth, params=params)

    return requests.request(
        method, endpoint, headers=headers, auth=auth, json=params)


def discover(discover_system: bool = True) -> Discovery:
    """
    Discover AWS capabilities from this extension as well, if a aws
    configuration is available, some information about the AWS environment.
    """
    logger.info("Discovering capabilities from chaostoolkit-aws")

    discovery = initialize_discovery_result(
        "chaostoolkit-aws", __version__, "aws")
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
    activities.extend(discover_probes("chaosaws.asg.probes"))
    activities.extend(discover_actions("chaosaws.awslambda.actions"))
    activities.extend(discover_probes("chaosaws.awslambda.probes"))

    return activities
