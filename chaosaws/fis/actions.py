from typing import Dict, List, Optional, Union

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "start_experiment",
    "stop_experiment",
    "stop_experiments_by_tags",
    "start_stress_pod_delete_scenario",
    "start_availability_zone_power_interruption_scenario",
]


def start_experiment(
    experiment_template_id: str,
    client_token: str = None,
    tags: Union[str, Dict[str, str]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Starts running an experiment from the specified experiment template.

    :param experiment_template_id: str representing the id of the experiment template
        to run
    :param client_token: str representing the unique identifier for this experiment run.
        If a value is not provided, boto3 generates one for you
    :param tags: str | Dict[str, str] representing tags to apply to the experiment that is
        started
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon starting the
        experiment

    Examples
    --------
    >>> start_experiment(
    ...     experiment_template_id="EXT6oWVA1WrLNy4XS"
    ... )
    {
    'ResponseMetadata': {'RequestId': '1ceaedae-5897-4b64-9ade-9e94449f1262',
    'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Thu, 12 Aug 2021 14:21:19 GMT',
    ...
    'experiment': {'id': 'EXPXDPecuQBFiZs1Jz',
    'experimentTemplateId': 'EXT6oWVA1WrLNy4XS',
    ...
    }

    >>> start_experiment(
    ...     experiment_template_id="EXT6oWVA1WrLNy4XS",
    ...     client_token="my-unique-token",
    ...     tags={"a-key": "a-value"}
    ... )
    """

    if not experiment_template_id:
        raise FailedActivity(
            "You must pass a valid experiment template id, id provided was empty"
        )

    tags = convert_tags(tags)

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    params = {"experimentTemplateId": experiment_template_id}
    if client_token:
        params["clientToken"] = client_token
    if tags:
        params["tags"] = tags

    try:
        return fis_client.start_experiment(**params)
    except Exception as ex:
        raise FailedActivity(f"Start Experiment failed, reason was: {ex}")


def stop_experiment(
    experiment_id: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Stops the specified experiment.

    :param experiment_id: str representing the running experiment to stop
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon stopping the
        experiment

    Examples
    --------
    >>> stop_experiment(experiment_id="EXPTUCK2dxepXgkR38")
    {'ResponseMetadata': {'RequestId': 'e5e9f9a9-f4d0-4d72-8704-1f26cc8b6ad6',
    'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Fri, 13 Aug 2021 09:12:17 GMT',
    ...'experiment': {'id': 'EXPTUCK2dxepXgkR38',
    'experimentTemplateId': 'EXT6oWVA1WrLNy4XS', ... }
    """
    if not experiment_id:
        raise FailedActivity(
            "You must pass a valid experiment id, id provided was empty"
        )

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    try:
        return fis_client.stop_experiment(id=experiment_id)
    except Exception as ex:
        raise FailedActivity(f"Stop Experiment failed, reason was: {ex}")


def stop_experiments_by_tags(
    tags: Union[str, Dict[str, str]],
    delete_templates: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Stops the experiments matching the given tags.

    Useful in rollbacks when experiment id isn't known.

    :param tags: str | Dict[str, str] representing tags to lookup experiments
    :param tags: Dict[str, str] representing tags to lookup experiments
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon stopping the
        experiment

    Examples
    --------
    >>> stop_experiments_by_tags(tags={"mytarget": "123"})
    [{'ResponseMetadata': {'RequestId': 'e5e9f9a9-f4d0-4d72-8704-1f26cc8b6ad6',
    'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Fri, 13 Aug 2021 09:12:17 GMT',
    ...'experiment': {'id': 'EXPTUCK2dxepXgkR38',
    'experimentTemplateId': 'EXT6oWVA1WrLNy4XS', ... }]
    """
    tags = convert_tags(tags)

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    try:
        experiments = fis_client.list_experiments(maxResults=100)
    except Exception as ex:
        raise FailedActivity(f"Listing Experiments failed, reason was: {ex}")

    stopped = []
    for x in experiments["experiments"]:
        print(x)
        try:
            if x["tags"] == tags:
                status = x["state"]["status"]
                if status in ("pending", "initiating", "running", "completed"):
                    result = fis_client.stop_experiment(id=x["id"])
                    stopped.append(result)
        except Exception as ex:
            raise FailedActivity(f"Stop Experiment failed, reason was: {ex}")

    return stopped


def start_stress_pod_delete_scenario(
    label_selector: str,
    tags: Union[str, Dict[str, str]],
    role_arn: str,
    log_group_arn: str,
    cluster_identifier: str,
    namespace: str = "default",
    service_account: str = "default",
    client_token: str = "",
    description: str = "Delete one or more EKS pods",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Create the 'EKS Stress: Pod Delete' template and start running it now

    :param label_selector: k=v string to identify the target pod
    :param tags: str | Dict[str, str] representing tags to lookup experiments
    :param namespace: pod namespace
    :param cluster_identifier: cluster identifier where the pod runs
    :param service_account: service account name
    :param role_arn: role ARN
    :param client_token: str representing the unique identifier for this experiment run.
        If a value is not provided, boto3 generates one for you
    :param description: friendly description for the template
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon starting the
        experiment
    """
    tags = convert_tags(tags)

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    scenario_tags = {"chaosengineering": "true", "chaostoolkit": "true"}
    scenario_tags.update(tags)

    params = dict(
        description=description,
        targets={
            "EksPodDeleteTarget": {
                "resourceType": "aws:eks:pod",
                "selectionMode": "ALL",
                "parameters": {
                    "clusterIdentifier": cluster_identifier,
                    "namespace": namespace,
                    "selectorType": "labelSelector",
                    "selectorValue": label_selector,
                },
            }
        },
        actions={
            "EksPodDelete": {
                "actionId": "aws:eks:pod-delete",
                "parameters": {"kubernetesServiceAccount": service_account},
                "targets": {"Pods": "EksPodDeleteTarget"},
            }
        },
        roleArn=role_arn,
        stopConditions=[{"source": "none"}],
        tags=scenario_tags,
        logConfiguration={
            "logSchemaVersion": 2,
            "cloudWatchLogsConfiguration": {"logGroupArn": log_group_arn},
        },
    )

    if client_token:
        params["clientToken"] = client_token

    template = fis_client.create_experiment_template(**params)

    experiment_template_id = template["experimentTemplate"]["id"]

    logger.debug(f"FIS Template {experiment_template_id} created")

    params = {"experimentTemplateId": experiment_template_id}
    if client_token:
        params["clientToken"] = client_token
    if tags:
        params["tags"] = tags

    try:
        return fis_client.start_experiment(**params)
    except Exception as ex:
        raise FailedActivity(f"Start Experiment failed, reason was: {ex}")


def start_availability_zone_power_interruption_scenario(
    az: str,
    tags: Union[str, Dict[str, str]],
    role_arn: str,
    duration: str = "PT30M",
    target_iam_roles: bool = False,
    iam_roles: Optional[List[str]] = None,
    target_subnet: bool = True,
    target_ebs_volumes: bool = True,
    target_ec2_instances: bool = True,
    target_asg: bool = True,
    target_asg_ec2_instances: bool = True,
    target_rds_cluster: bool = True,
    target_easticache_cluster: bool = True,
    log_group_arn: str = "",
    client_token: str = "",
    description: str = "Affect multiple resource types in a single AZ to approximate power interruption",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Create the 'AZ Availability: Power Interruption' template and start running
    it now

    :param az: availability zone to disrupt
    :param tags: str | Dict[str, str] representing tags to lookup experiments
    :param duration: disruption duration
    :param role_arn: role ARN
    :param target_iam_roles: bool whether or not the experiment must target IAM roles. `iam_roles` must then be provided
    :param iam_roles: List[str] list of roles ARN to target
    :param target_subnet: bool whether or not the experiment must target subnets
    :param target_ebs_volumes: bool whether or not the experiment must target EBS volumes
    :param target_ec2_instances: bool whether or not the experiment must target ECS instances
    :param target_asg: bool whether or not the experiment must target ASG
    :param target_asg_ec2_instances: bool whether or not the experiment must target ASG EC2 instances
    :param target_rds_cluster: bool whether or not the experiment must target RDS clusters
    :param target_easticache_cluster: bool whether or not the experiment must target ElastiCache clusters
    :param log_group_arn: str ARN for a cloud watch log configuration
    :param client_token: str representing the unique identifier for this experiment run.
        If a value is not provided, boto3 generates one for you
    :param description: friendly description for the template
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon starting the
        experiment
    """
    tags = convert_tags(tags)

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    scenario_tags = {"chaosengineering": "true", "chaostoolkit": "true"}
    scenario_tags.update(tags)

    targets = {}
    actions = {}

    if target_iam_roles and iam_roles:
        targets["IAM-role"] = {
            "resourceType": "aws:iam:role",
            "resourceArns": iam_roles,
            "selectionMode": "ALL",
        }
        actions["Pause-Instance-Launches"] = {
            "actionId": "aws:ec2:api-insufficient-instance-capacity-error",
            "parameters": {
                "availabilityZoneIdentifiers": az,
                "duration": duration,
                "percentage": "100",
            },
            "targets": {"Roles": "IAM-role"},
        }

    if target_ebs_volumes:
        targets["EBS-Volumes"] = {
            "resourceType": "aws:ec2:ebs-volume",
            "resourceTags": {"AzImpairmentPower": "ApiPauseVolume"},
            "selectionMode": "COUNT(1)",
            "parameters": {"availabilityZoneIdentifier": az},
            "filters": [
                {"path": "Attachments.DeleteOnTermination", "values": ["false"]}
            ],
        }
        actions["Pause-EBS-IO"] = {
            "actionId": "aws:ebs:pause-volume-io",
            "parameters": {"duration": duration},
            "targets": {"Volumes": "EBS-Volumes"},
            "startAfter": ["Stop-Instances", "Stop-ASG-Instances"],
        }

    if target_ec2_instances:
        targets["EC2-Instances"] = {
            "resourceType": "aws:ec2:instance",
            "resourceTags": {"AzImpairmentPower": "StopInstances"},
            "filters": [
                {"path": "State.Name", "values": ["running"]},
                {"path": "Placement.AvailabilityZone", "values": [az]},
            ],
            "selectionMode": "ALL",
        }
        actions["Stop-Instances"] = {
            "actionId": "aws:ec2:stop-instances",
            "parameters": {
                "completeIfInstancesTerminated": "true",
                "startInstancesAfterDuration": duration,
            },
            "targets": {"Instances": "EC2-Instances"},
        }

    if target_asg:
        targets["ASG"] = {
            "resourceType": "aws:ec2:autoscaling-group",
            "resourceTags": {"AzImpairmentPower": "IceAsg"},
            "selectionMode": "ALL",
        }
        actions["Pause-ASG-Scaling"] = {
            "actionId": "aws:ec2:asg-insufficient-instance-capacity-error",
            "parameters": {
                "availabilityZoneIdentifiers": az,
                "duration": duration,
                "percentage": "100",
            },
            "targets": {"AutoScalingGroups": "ASG"},
        }

    if target_asg_ec2_instances:
        targets["ASG-EC2-Instances"] = {
            "resourceType": "aws:ec2:instance",
            "resourceTags": {"AzImpairmentPower": "IceAsg"},
            "filters": [
                {"path": "State.Name", "values": ["running"]},
                {"path": "Placement.AvailabilityZone", "values": [az]},
            ],
            "selectionMode": "ALL",
        }
        actions["Stop-ASG-Instances"] = {
            "actionId": "aws:ec2:stop-instances",
            "parameters": {
                "completeIfInstancesTerminated": "true",
                "startInstancesAfterDuration": duration,
            },
            "targets": {"Instances": "ASG-EC2-Instances"},
        }

    if target_rds_cluster:
        targets["RDS-Cluster"] = {
            "resourceType": "aws:rds:cluster",
            "resourceTags": {"AzImpairmentPower": "DisruptRds"},
            "selectionMode": "ALL",
            "parameters": {"writerAvailabilityZoneIdentifiers": az},
        }
        actions["Failover-RDS"] = {
            "actionId": "aws:rds:failover-db-cluster",
            "parameters": {},
            "targets": {"Clusters": "RDS-Cluster"},
        }

    if target_easticache_cluster:
        targets["ElastiCache-Cluster"] = {
            "resourceType": "aws:elasticache:redis-replicationgroup",
            "resourceTags": {"AzImpairmentPower": "DisruptElasticache"},
            "selectionMode": "ALL",
            "parameters": {"availabilityZoneIdentifier": az},
        }
        actions["Pause-ElastiCache"] = {
            "actionId": "aws:elasticache:interrupt-cluster-az-power",
            "parameters": {"duration": duration},
            "targets": {"ReplicationGroups": "ElastiCache-Cluster"},
        }

    if target_subnet:
        targets["Subnet"] = {
            "resourceType": "aws:ec2:subnet",
            "resourceTags": {"AzImpairmentPower": "DisruptSubnet"},
            "filters": [{"path": "AvailabilityZone", "values": [az]}],
            "selectionMode": "ALL",
            "parameters": {},
        }
        actions["Pause-network-connectivity"] = {
            "actionId": "aws:network:disrupt-connectivity",
            "parameters": {"duration": "PT2M", "scope": "all"},
            "targets": {"Subnets": "Subnet"},
        }

    params = {
        "targets": targets,
        "actions": actions,
        "stopConditions": [{"source": "none"}],
        "roleArn": role_arn,
        "tags": scenario_tags,
        "experimentOptions": {
            "accountTargeting": "single-account",
            "emptyTargetResolutionMode": "skip",
        },
        "description": description,
    }

    if log_group_arn:
        params["logConfiguration"] = {
            "logSchemaVersion": 2,
            "cloudWatchLogsConfiguration": {"logGroupArn": log_group_arn},
        }

    if client_token:
        params["clientToken"] = client_token

    template = fis_client.create_experiment_template(**params)

    experiment_template_id = template["experimentTemplate"]["id"]

    logger.debug(f"FIS Template {experiment_template_id} created")

    params = {"experimentTemplateId": experiment_template_id}
    if client_token:
        params["clientToken"] = client_token
    if tags:
        params["tags"] = scenario_tags

    try:
        return fis_client.start_experiment(**params)
    except Exception as ex:
        raise FailedActivity(f"Start Experiment failed, reason was: {ex}")


###############################################################################
# Private functions
###############################################################################
def convert_tags(tags: Union[str, Dict[str, str]]) -> Dict[str, str]:
    """
    Convert a `k=v,x=y` string into a dictionary
    """
    if isinstance(tags, dict):
        return tags

    result = {}
    for t in tags.split(","):
        k, v = t.split("=", 1)
        result[k] = v

    return result
