from typing import Any, Dict, Optional, Union

from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client, get_logger, time_to_datetime

__all__ = [
    "get_incidents",
    "get_active_incidents",
    "get_resolved_incidents",
    "has_incident_been_opened",
    "has_incident_been_resolved",
    "get_active_incident_items",
    "get_resolved_incident_items",
]

logger = get_logger()


def get_incidents(
    impact: int = 1,
    status: str = "OPEN",
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Return a list of incidents by their `impact`, `status` and created within
    the given window.

    The window is either a string such as `3 minutes` and is relative to now
    minues these 3 minutes. Or it can be a number of seconds as real value.

    You may restrict to the incidents created by a given resouce/role by
    setting the `created_by` arn.

    See also:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm-incidents.html
    """  # noqa: E501
    end = time_to_datetime("now")
    start = time_to_datetime(created_in_the_last, offset=end)

    filters = [
        {"condition": {"equals": {"integerValues": [impact]}}, "key": "impact"},
        {"condition": {"after": start}, "key": "creationTime"},
        {"condition": {"equals": {"stringValues": [status]}}, "key": "status"},
    ]

    if created_by:
        filters.append(
            {
                "condition": {"equals": {"stringValues": [created_by]}},
                "key": "createdBy",
            }
        )

    client = aws_client("ssm-incidents", configuration, secrets)
    try:
        logger.debug(
            f"Requesting incidents between {start} and {end} with impact "
            f"{impact} and status {status} and created by {created_by or 'n/a'}"
        )
        response = client.list_incident_records(
            filters=filters,
            maxResults=10,
        )
        logger.debug(
            f"Found {len(response['incidentRecordSummaries'])} incidents"
        )
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS SSM Incidents API", exc_info=True)
        raise ActivityFailed(f"SSM Incidents API failed: {str(e)}")

    return response


def get_active_incidents(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Return a list of opened incidents by their `impact` and created within the
    given window.

    The window is either a string such as `3 minutes` and is relative to now
    minues these 3 minutes. Or it can be a number of seconds as real value.

    You may restrict to the incidents created by a given resouce/role by
    setting the `created_by` arn.

    See also:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm-incidents.html
    """  # noqa: E501
    return get_incidents(
        impact,
        "OPEN",
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )


def get_resolved_incidents(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Return a list of resolved incidents by their `impact` and created within the
    given window.

    The window is either a string such as `3 minutes` and is relative to now
    minues these 3 minutes. Or it can be a number of seconds as real value.

    You may restrict to the incidents created by a given resouce/role by
    setting the `created_by` arn.

    See also:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm-incidents.html
    """  # noqa: E501
    return get_incidents(
        impact,
        "RESOLVED",
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )


def has_incident_been_opened(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    incidents = get_incidents(
        impact,
        "OPEN",
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )

    return len(incidents["incidentRecordSummaries"]) > 0


def has_incident_been_resolved(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> bool:
    incidents = get_incidents(
        impact,
        "RESOLVED",
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )

    return len(incidents["incidentRecordSummaries"]) > 0


def get_active_incident_items(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Retrieve the list of items related to the most recent active incident
    matching the criteria.
    """
    incidents = get_active_incidents(
        impact,
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )

    arn = incidents["incidentRecordSummaries"][0]["arn"]

    client = aws_client("ssm-incidents", configuration, secrets)
    try:
        response = client.list_incident_records(
            incidentRecordArn=arn,
            maxResults=10,
        )
        logger.debug(f"Found {len(response['relatedItems'])} items")
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS SSM Incidents API", exc_info=True)
        raise ActivityFailed(f"SSM Incidents API failed: {str(e)}")

    return response


def get_resolved_incident_items(
    impact: int = 1,
    created_in_the_last: Union[str, float] = "3 minutes",
    created_by: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Retrieve the list of items related to the most recent resolved incident
    matching the criteria.
    """
    incidents = get_resolved_incidents(
        impact,
        created_in_the_last,
        created_by,
        configuration=configuration,
        secrets=secrets,
    )

    arn = incidents["incidentRecordSummaries"][0]["arn"]

    client = aws_client("ssm-incidents", configuration, secrets)
    try:
        logger.debug(f"Looking up items for incident {arn}")
        response = client.list_related_items(
            incidentRecordArn=arn,
            maxResults=10,
        )
        logger.debug(f"Found {len(response['relatedItems'])} items")
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS SSM Incidents API", exc_info=True)
        raise ActivityFailed(f"SSM Incidents API failed: {str(e)}")

    return response
