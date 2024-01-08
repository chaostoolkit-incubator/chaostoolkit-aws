from datetime import datetime, timedelta
from typing import Any, Dict, List

from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "get_cost_and_usage",
]


def get_cost_and_usage(
    window_period: int = 86400,
    window_offset: int = 0,
    granularity: str = "DAILY",
    group_by: List[Dict[str, str]] = None,
    metrics: List[str] = None,
    filter: Dict[str, Any] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Retrieve the cost/usage for your account based on given filters and
    parameters.
    """
    end_time = datetime.utcnow() - timedelta(seconds=window_offset)
    start_time = end_time - timedelta(seconds=window_period)

    print(start_time.date().isoformat(), end_time.date().isoformat())
    client = aws_client("ce", configuration, secrets)

    r = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_time.date().isoformat(),
            "End": end_time.date().isoformat(),
        },
        Granularity=granularity,
        Filter=filter,
        Metrics=metrics,
        GroupBy=group_by,
    )

    return r


def get_eks_cluster_usage_for_today(az: str = "", tag: str = "") -> AWSResponse:
    filters = {}

    if az:
        filters["Dimensions"] = {
            "Key": "AZ",
            "MatchOptions": ["EQUALS"],
            "Values": [az],
        }

    if tag:
        filters["Tags"] = convert_tag(tag)
    
    filters.append({
        "And": [
            {
                "Dimensions": {
                    "Key": "",
                    "Values": []
                }
            }
        ]
    })

    print(filters)

    return get_cost_and_usage(
        window_period=86400,
        window_offset=0,
        granularity="DAILY",
        group_by=[
            {
                "Type": "DIMENSION",
                "Key": "USAGE_TYPE"
            }
        ],
        metrics=["AmortizedCost"],
        filter=filters
    )


def convert_tag(tag: str) -> Dict[str, str]:
    """
    Convert a `k=v` string into a dictionary
    """
    
    return {
        "Key": k,
        "Values": [v]
    }



r = get_eks_cluster_usage_for_today(
    tag="alpha.eksctl.io/cluster-name=amazing-sheepdog-1681288074"
)
print(r)
