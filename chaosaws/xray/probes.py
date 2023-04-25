import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client

__all__ = [
    "get_traces",
    "get_traces_summaries",
    "get_most_recent_trace",
    "get_service_graph",
]


def get_traces_summaries(
    start_time: Union[str, float] = "3 minutes",
    end_time: Union[str, float] = "now",
    time_range_type: str = "TraceId",
    filter_expression: str = 'groupname = "Default"',
    sampling: bool = False,
    sampling_strategy: Optional[Dict[str, float]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Return a list of recent XRay trace summaries within the given time range.

    Time can be given as a float, which is an absolute Unix timestamp (UTC) or
    as a string representing a relative period such as "1 minute".

    Supported units are: seconds, minutes, hours and days. Plural and singular.

    Be careful about what you ask for, this can lead to a huge amount of
    traces being returned. Try to filter using `filter_expression` and/or
    `sampling`.

    The possbile alarm state values are described in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/xray/client/get_trace_summaries.html
    """  # noqa: E501
    client = aws_client("xray", configuration, secrets)
    try:
        end = time_to_datetime(end_time)
        start = time_to_datetime(start_time, offset=end)
        logger.debug(f"Requesting traces between {start} and {end}")
        response = client.get_trace_summaries(
            StartTime=start,
            EndTime=end,
            TimeRangeType=time_range_type,
            FilterExpression=filter_expression,
            Sampling=sampling,
            SamplingStrategy=sampling_strategy or {},
        )
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS XRay API", exc_info=True)
        raise ActivityFailed(f"XRay trace summaries failed: {str(e)}")

    return response


def get_traces(
    start_time: Union[str, float] = "3 minutes",
    end_time: Union[str, float] = "now",
    time_range_type: str = "TraceId",
    filter_expression: str = 'groupname = "Default"',
    sampling: bool = False,
    sampling_strategy: Optional[Dict[str, float]] = None,
    quantity: int = 5,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Return a list of recent XRay traces within the given time range.

    Time can be given as a float, which is an absolute Unix timestamp (UTC) or
    as a string representing a relative period such as "1 minute".

    Supported units are: seconds, minutes, hours and days. Plural and singular.

    This will never return more than 5 traces as per the limits set by the AWS
    API. It will always pick the 5 newest.

    The possbile alarm state values are described in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/xray/client/batch_get_traces.html
    """  # noqa: E501
    summaries = get_traces_summaries(
        start_time,
        end_time,
        time_range_type,
        filter_expression,
        sampling,
        sampling_strategy,
        configuration,
        secrets,
    )
    quantity = min(quantity, 5)
    trace_ids = [s["Id"] for s in summaries.get("TraceSummaries", [])[-quantity:]]
    client = aws_client("xray", configuration, secrets)
    try:
        response = client.batch_get_traces(TraceIds=trace_ids)
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS XRay API", exc_info=True)
        raise ActivityFailed(f"XRay batch traces failed: {str(e)}")

    return response


def get_most_recent_trace(
    start_time: Union[str, float] = "3 minutes",
    end_time: Union[str, float] = "now",
    time_range_type: str = "TraceId",
    filter_expression: str = 'groupname = "Default"',
    sampling: bool = False,
    sampling_strategy: Optional[Dict[str, float]] = None,
    raw_segments: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Return a list of recent XRay traces within the given time range.

    Time can be given as a float, which is an absolute Unix timestamp (UTC) or
    as a string representing a relative period such as "1 minute".

    Supported units are: seconds, minutes, hours and days. Plural and singular.

    Be careful about what you ask for, this can lead to a huge amount of
    traces being returned. Try to filter using `filter_expression`.

    The response is the AWS response as-is. The content of each segments of the
    trace are encoded as a json string. By setting `raw_segments` you ask for
    the list of segment documents decoded. Useful in an hypothesis scenario
    with a tolerance set to a jsonpath for instance.

    The possbile alarm state values are described in the documentation
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/xray/client/batch_get_traces.html
    """  # noqa: E501
    trace = get_traces(
        start_time,
        end_time,
        time_range_type,
        filter_expression,
        sampling,
        sampling_strategy,
        1,
        configuration,
        secrets,
    )

    if not raw_segments:
        return trace

    if not trace["Traces"]:
        return {}

    segments = []
    for s in trace["Traces"][0]["Segments"]:
        segments.append(json.loads(s["Document"]))
    return segments


def get_service_graph(
    start_time: Union[str, float] = "3 minutes",
    end_time: Union[str, float] = "now",
    group_name: Optional[str] = "Default",
    group_arn: Optional[str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Return a service graph for a given group at a given moment.

    See more information:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/xray/client/get_service_graph.html
    """  # noqa: E501
    client = aws_client("xray", configuration, secrets)
    try:
        end = time_to_datetime(end_time)
        start = time_to_datetime(start_time, offset=end)
        logger.debug(f"Requesting service graph between {start} and {end}")
        response = client.get_service_graph(
            StartTime=start,
            EndTime=end,
            GroupName=group_name or "",
            GroupARN=group_arn or "",
        )
    except Exception as e:
        # catchall as boto3 exception management is so poorly documented
        logger.debug("Failed to call AWS XRay API", exc_info=True)
        raise ActivityFailed(f"XRay service graph failed: {str(e)}")

    return response


###############################################################################
# Private functions
###############################################################################
def time_to_datetime(
    ts: Union[str, float], offset: Optional[datetime] = None
) -> datetime:
    if isinstance(ts, float):
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if ts == "now":
        return datetime.utcnow().replace(tzinfo=timezone.utc)

    offset = offset or datetime.utcnow().replace(tzinfo=timezone.utc)
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

    return offset - timedelta(seconds=duration * delta)
