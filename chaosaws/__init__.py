# -*- coding: utf-8 -*-
from typing import Any, Dict, List

import boto3
from chaoslib.discovery.discover import discover_actions, discover_probes, \
    initialize_discovery_result
from chaoslib.exceptions import DiscoveryFailed
from chaoslib.types import Configuration, Discovery, DiscoveredActivities, \
    DiscoveredSystemInfo, Secrets
from logzero import logger

__version__ = '0.1.0'
__all__ = ["__version__", "discover", "aws_client"]


def aws_client(resource_name: str, configuration: Configuration=None,
               secrets: Secrets=None):
    """
    Create a boto3 client.
    """
    configuration = configuration or {}
    region = configuration.get("aws_region", "us-east-1")

    creds = dict(
        aws_access_key_id=None, aws_secret_access_key=None,
        aws_session_token=None)
    if secrets:
        creds["aws_access_key_id"] = secrets.get("aws_access_key_id")
        creds["aws_secret_access_key"] = secrets.get("aws_secret_access_key")
        creds["aws_session_token"] = secrets.get("aws_session_token")

    return boto3.resource(resource_name, region_name=region, **creds)


def discover(discover_system: bool = True) -> Discovery:
    """
    Discover AWS capabilities from this extension as well, if a aws
    configuration is available, some information about the AWS environment.
    """
    logger.info("Discovering capabilities from chaostoolkit-aws")

    discovery = initialize_discovery_result(
        "chaostoolkit-aws", __version__, "aws")
    discovery["activities"].extend(load_exported_activities())
    if discover_system:
        discovery["system"] = explore_aws_system()

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
    return activities


def explore_aws_system() -> DiscoveredSystemInfo:
    """
    Fetch information from the current AWS context.
    """
    logger.info("Discovering AWS system")
    # TBD
    return {}
