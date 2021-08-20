import random
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "deregister_target",
    "set_security_groups",
    "set_subnets",
    "delete_load_balancer",
]


def deregister_target(
    tg_name: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """Deregisters one random target from target group"""
    client = aws_client("elbv2", configuration, secrets)
    tg_arn = get_target_group_arns(tg_names=[tg_name], client=client)
    tg_health = get_targets_health_description(tg_arns=tg_arn, client=client)
    random_target = random.choice(tg_health[tg_name]["TargetHealthDescriptions"])

    logger.debug(
        "Deregistering target {} from target group {}".format(
            random_target["Target"]["Id"], tg_name
        )
    )

    try:
        return client.deregister_targets(
            TargetGroupArn=tg_arn[tg_name],
            Targets=[
                {
                    "Id": random_target["Target"]["Id"],
                    "Port": random_target["Target"]["Port"],
                }
            ],
        )
    except ClientError as e:
        raise FailedActivity(
            "Exception detaching {}: {}".format(tg_name, e.response["Error"]["Message"])
        )


def set_security_groups(
    load_balancer_names: List[str],
    security_group_ids: List[str],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Changes the security groups for the specified load balancer(s).
    This action will replace the existing security groups on an application
    load balancer with the specified security groups.

    Parameters:
        - load_balancer_names: a list of load balancer names
        - security_group_ids: a list of security group ids

    returns:
        [
            {
                'LoadBalancerArn': 'string',
                'SecurityGroupIds': ['sg-0000000', 'sg-0000001']
            },
            ...
        ]
    """
    security_group_ids = get_security_groups(
        security_group_ids, aws_client("ec2", configuration, secrets)
    )

    client = aws_client("elbv2", configuration, secrets)
    load_balancers = get_load_balancer_arns(load_balancer_names, client)

    if load_balancers.get("network", []):
        raise FailedActivity("Cannot change security groups of network load balancers.")

    results = []
    for load_balancer in load_balancers["application"]:
        response = client.set_security_groups(
            LoadBalancerArn=load_balancer, SecurityGroups=security_group_ids
        )

        # add load balancer arn to response
        response["LoadBalancerArn"] = load_balancer
        results.append(response)
    return results


def set_subnets(
    load_balancer_names: List[str],
    subnet_ids: List[str],
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Changes the subnets for the specified application load balancer(s)
    This action will replace the existing security groups on an application
    load balancer with the specified security groups.

    Parameters:
        - load_balancer_names: a list of load balancer names
        - subnet_ids: a list of subnet ids

    returns:
        [
            {
                'LoadBalancerArn': 'string',
                'AvailabilityZones': {
                    'ZoneName': 'string',
                    'SubnetId': 'string',
                    'LoadBalancerAddresses': [
                        {
                            'IpAddress': 'string',
                            'AllocationId': 'string'
                        }
                    ]
                }
            },
            ...
        ]
    """
    subnet_ids = get_subnets(subnet_ids, aws_client("ec2", configuration, secrets))

    client = aws_client("elbv2", configuration, secrets)
    load_balancers = get_load_balancer_arns(load_balancer_names, client)

    if load_balancers.get("network", []):
        raise FailedActivity("Cannot change subnets of network load balancers.")

    results = []
    for load_balancer in load_balancers["application"]:
        response = client.set_subnets(LoadBalancerArn=load_balancer, Subnets=subnet_ids)
        response["LoadBalancerArn"] = load_balancer
        results.append(response)
    return results


def delete_load_balancer(
    load_balancer_names: List[str],
    configuration: Configuration = None,
    secrets: Secrets = None,
):
    """
    Deletes the provided load balancer(s).

    Parameters:
        - load_balancer_names: a list of load balancer names
    """
    client = aws_client("elbv2", configuration, secrets)
    load_balancers = get_load_balancer_arns(load_balancer_names, client)

    for k, v in load_balancers.items():
        if k not in ("application", "network"):
            continue

        for load_balancer in v:
            logger.debug("Deleting load balancer %s" % load_balancer)
            client.delete_load_balancer(LoadBalancerArn=load_balancer)


###############################################################################
# Private functions
###############################################################################
def get_load_balancer_arns(
    load_balancer_names: List[str], client: boto3.client
) -> Dict[str, List[str]]:
    """
    Returns load balancer arns categorized by the type of load balancer

    return structure:
    {
        'network': ['load balancer arn'],
        'application': ['load balancer arn']
    }
    """
    results = {}
    logger.debug(f"Searching for load balancer name(s): {load_balancer_names}.")

    try:
        response = client.describe_load_balancers(Names=load_balancer_names)

        for lb in response["LoadBalancers"]:
            if lb["State"]["Code"] != "active":
                raise FailedActivity(
                    "Invalid state for load balancer {}: "
                    "{} is not active".format(
                        lb["LoadBalancerName"], lb["State"]["Code"]
                    )
                )
            results.setdefault(lb["Type"], []).append(lb["LoadBalancerArn"])
            results.setdefault("Names", []).append(lb["LoadBalancerName"])
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])

    missing_lbs = [
        load_balancer
        for load_balancer in load_balancer_names
        if load_balancer not in results["Names"]
    ]
    if missing_lbs:
        raise FailedActivity(f"Unable to locate load balancer(s): {missing_lbs}")

    if not results:
        raise FailedActivity(
            "Unable to find any load balancer(s) matching name(s): {}".format(
                load_balancer_names
            )
        )

    return results


def get_target_group_arns(tg_names: List[str], client: boto3.client) -> Dict:
    """
    Return list of target group ARNs based on list of target group names

    return structure:
    {
        "TargetGroupName": "TargetGroupArn",
        ....
    }
    """
    logger.debug(f"Target group name(s): {str(tg_names)} Looking for ARN")
    res = client.describe_target_groups(Names=tg_names)
    tg_arns = {}

    for tg in res["TargetGroups"]:
        tg_arns[tg["TargetGroupName"]] = tg["TargetGroupArn"]
    logger.debug(f"Target groups ARN: {str(tg_arns)}")

    return tg_arns


def get_targets_health_description(tg_arns: Dict, client: boto3.client) -> Dict:
    """
    Return TargetHealthDescriptions by targetgroups
    Structure:
    {
        "TargetGroupName": {
            "TargetGroupArn": value,
            "TargetHealthDescriptions": TargetHealthDescriptions[]
        },
        ....
    }
    """
    logger.debug(f"Target group ARN: {str(tg_arns)} Getting health descriptions")
    tg_health_descr = {}

    for tg in tg_arns:
        tg_health_descr[tg] = {}
        tg_health_descr[tg]["TargetGroupArn"] = tg_arns[tg]
        tg_health_descr[tg]["TargetHealthDescriptions"] = client.describe_target_health(
            TargetGroupArn=tg_arns[tg]
        )["TargetHealthDescriptions"]
    logger.debug(f"Health descriptions for target group(s) are: {str(tg_health_descr)}")
    return tg_health_descr


def get_security_groups(sg_ids: List[str], client: boto3.client) -> List[str]:
    try:
        response = client.describe_security_groups(GroupIds=sg_ids)["SecurityGroups"]
        results = [r["GroupId"] for r in response]
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])

    missing_sgs = [s for s in sg_ids if s not in results]
    if missing_sgs:
        raise FailedActivity(f"Invalid security group id(s): {missing_sgs}")
    return results


def get_subnets(subnet_ids: List[str], client: boto3.client) -> List[str]:
    try:
        response = client.describe_subnets(SubnetIds=subnet_ids)["Subnets"]
        results = [r["SubnetId"] for r in response]
    except ClientError as e:
        raise FailedActivity(e.response["Error"]["Message"])

    missing_subnets = [s for s in subnet_ids if s not in results]
    if missing_subnets:
        raise FailedActivity(f"Invalid subnet id(s): {missing_subnets}")
    return results
