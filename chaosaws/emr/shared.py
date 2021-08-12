from typing import List

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from logzero import logger

from chaosaws.types import AWSResponse


def describe_emr_cluster(client: boto3.client, cluster_id: str) -> AWSResponse:
    try:
        return client.describe_cluster(ClusterId=cluster_id)
    except ClientError as e:
        logger.exception(e.response["Error"]["Message"])
        raise FailedActivity(e.response["Error"]["Message"])


def list_emr_instances(
    client: boto3.client,
    cluster_id: str,
    group_id: str = None,
    group_type: str = None,
    fleet_id: str = None,
    fleet_type: str = None,
    instance_states: List[str] = None,
) -> AWSResponse:
    params = {
        "ClusterId": cluster_id,
        **({"InstanceGroupId": group_id} if group_id else {}),
        **({"InstanceGroupType": group_type} if group_type else {}),
        **({"InstanceFleetId": fleet_id} if fleet_id else {}),
        **({"InstanceFleetType": fleet_type} if fleet_type else {}),
        **({"InstanceStates": instance_states} if instance_states else {}),
    }

    instances = []

    def _list(marker: str = None):
        if marker:
            params["Marker"] = marker

        try:
            response = client.list_instances(**params)

            for r in response["Instances"]:
                instances.append(r)

            marker = response.get("Marker")
            if marker:
                _list(marker)
        except ClientError as e:
            logger.exception(e.response["Error"]["Message"])
            raise FailedActivity(e.response["Error"]["Message"])

    _list()
    return {"Instances": instances}


def get_instance_fleet(
    client: boto3.client, cluster_id: str, fleet_id: str
) -> AWSResponse:
    fleets = {"InstanceFleets": None}

    def _list(marker: str = None):
        params = {"ClusterId": cluster_id, **({"Marker": marker} if marker else {})}

        try:
            response = client.list_instance_fleets(**params)
            for r in response["InstanceFleets"]:
                if r["Id"] == fleet_id:
                    fleets["InstanceFleets"] = r
                    break

            if response.get("Marker") and not fleets["InstanceFleets"]:
                _list(marker=response["Marker"])
        except ClientError as e:
            logger.exception(e.response["Error"]["Message"])
            raise FailedActivity(e.response["Error"]["Message"])

    _list()
    return fleets


def get_instance_group(
    client: boto3.client, cluster_id: str, group_id: str
) -> AWSResponse:
    groups = {"InstanceGroups": None}

    def _list(marker: str = None):
        params = {"ClusterId": cluster_id, **({"Marker": marker} if marker else {})}
        try:
            response = client.list_instance_groups(**params)
            for r in response["InstanceGroups"]:
                if r["Id"] == group_id:
                    groups["InstanceGroups"] = r
                    break

            if response.get("Marker") and not groups["InstanceGroups"]:
                _list(marker=response["Marker"])
        except ClientError as e:
            logger.exception(e.response["Error"]["Message"])
            raise FailedActivity(e.response["Error"]["Message"])

    _list()
    return groups
