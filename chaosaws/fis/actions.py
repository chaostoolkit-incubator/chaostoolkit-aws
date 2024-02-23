import json
import threading
import time
from typing import Dict, List, Optional, Union

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import (
    aws_client,
    convert_tags,
    get_logger,
    tags_as_key_value_pairs,
)
from chaosaws.types import AWSResponse

__all__ = [
    "start_experiment",
    "stop_experiment",
    "stop_experiments_by_tags",
    "start_stress_pod_delete_scenario",
    "start_availability_zone_power_interruption_scenario",
    "restore_availability_zone_power_after_interruption",
]

logger = get_logger()


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

    logger.debug(f"Trying to stop experiments which are supersets of {tags}")
    stopped = []
    template_ids = []
    for x in experiments["experiments"]:
        try:
            if tags.items() <= x["tags"].items():
                status = x["state"]["status"]
                if status in ("pending", "initiating", "running", "completed"):
                    result = fis_client.stop_experiment(id=x["id"])
                    stopped.append(result)
                    template_ids.append(x["experimentTemplateId"])
        except Exception as ex:
            raise FailedActivity(f"Stop Experiment failed, reason was: {ex}")

    logger.debug(f"Stopped experiments {stopped}")

    if delete_templates:
        logger.debug(f"Deleting experiments templates {template_ids}")

        for template_id in template_ids:
            try:
                fis_client.delete_experiment_template(id=template_id)
                logger.debug(f"Experiment template {template_id} deleted")
            except Exception as ex:
                raise FailedActivity(
                    f"Delete Experiment template {template_id} failed, "
                    f"reason was: {ex}"
                )

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
    tags: Union[str, Dict[str, str], None] = "",
    role_arn: Optional[str] = "",
    autocreate_necessary_role: bool = True,
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
    :param tags: str | Dict[str, str] | None representing tags to lookup experiments
    :param duration: disruption duration
    :param role_arn: role ARN, when provided `autocreate_necessary_role` is set to False
    :param autocreate_necessary_role: boolean that indicate the necessary role is automatically created if not passed as `role_arn`
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
    sts_client = aws_client(
        resource_name="sts", configuration=configuration, secrets=secrets
    )
    account_id = sts_client.get_caller_identity().get("Account")

    suffix = f"{threading.get_ident()}"

    tags = convert_tags(tags)

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    scenario_tags = {
        "chaosengineering": "true",
        "chaostoolkit": "true",
        "chaostoolkit-experiment-key": suffix,
    }
    scenario_tags.update(tags)
    tags_as_kv = tags_as_key_value_pairs(scenario_tags)
    logger.debug(f"FIS experiment tags {scenario_tags}")

    targets = {}
    actions = {}

    create_console_ebsvolume_policy = False
    create_console_ec2_policy = False
    enable_rds_policy = False
    create_console_elasticache_policy = False
    create_console_network_policy = False

    if role_arn:
        autocreate_necessary_role = False

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
        create_console_ebsvolume_policy = True
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
        create_console_ec2_policy = True
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
        enable_rds_policy = True
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
        create_console_elasticache_policy = True
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
        create_console_network_policy = True
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

    if autocreate_necessary_role:
        iam_client = aws_client(
            resource_name="iam", configuration=configuration, secrets=secrets
        )

        role_name = f"ChaosToolkit-FIS-{suffix}"

        assume_role_policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "fis.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )

        response = iam_client.create_role(
            Path="/service-role/",
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy,
            Description="Chaos Toolkit generated role for AWS FIS experiments",
            MaxSessionDuration=3 * 3600,  # 3 hours
            Tags=tags_as_kv,
        )

        role_arn = response["Role"]["Arn"]
        logger.debug(f"FIS Role created: {role_arn}")

        a, b, c = az.split("-", 2)
        target_region = f"{a}-{b}-{c[0]}"
        logger.debug(f"Target AZ {az}")
        logger.debug(f"Target region {target_region}")

        if create_console_ebsvolume_policy:
            response = iam_client.create_policy(
                PolicyName=f"FIS-Console-EBSPauseVolumeIO-{suffix}",
                PolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["ec2:DescribeVolumes"],
                                "Resource": "*",
                            },
                            {
                                "Effect": "Allow",
                                "Action": ["ec2:PauseVolumeIO"],
                                "Resource": f"arn:aws:ec2:{target_region}:{account_id}:volume/*",
                            },
                        ],
                    }
                ),
                Tags=tags_as_kv,
            )

            policy_arn = response["Policy"]["Arn"]
            logger.debug(f"Role policy created: {policy_arn}")

            response = iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn=policy_arn
            )

        if create_console_ec2_policy:
            response = iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorEC2Access",
            )

            response = iam_client.create_policy(
                PolicyName=f"FIS-Console-ICE-{suffix}",
                PolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "AllowInjectAPI",
                                "Effect": "Allow",
                                "Action": ["ec2:InjectApiError"],
                                "Resource": ["*"],
                                "Condition": {
                                    "ForAnyValue:StringEquals": {
                                        "ec2:FisActionId": [
                                            "aws:ec2:api-insufficient-instance-capacity-error",
                                            "aws:ec2:asg-insufficient-instance-capacity-error",
                                        ]
                                    }
                                },
                            },
                            {
                                "Sid": "DescribeAsg",
                                "Effect": "Allow",
                                "Action": [
                                    "autoscaling:DescribeAutoScalingGroups"
                                ],
                                "Resource": ["*"],
                            },
                        ],
                    }
                ),
                Tags=tags_as_kv,
            )

            policy_arn = response["Policy"]["Arn"]
            logger.debug(f"Role policy created: {policy_arn}")

            response = iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn=policy_arn
            )

        if create_console_elasticache_policy:
            response = iam_client.create_policy(
                PolicyName=f"FIS-Console-ElastiCache-{suffix}",
                PolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "AllowElastiCacheActions",
                                "Effect": "Allow",
                                "Action": [
                                    "elasticache:DescribeReplicationGroups",
                                    "elasticache:InterruptClusterAzPower",
                                ],
                                "Resource": [
                                    f"arn:aws:elasticache:{target_region}:{account_id}:replicationgroup:*"
                                ],
                            },
                            {
                                "Sid": "TargetResolutionByTags",
                                "Effect": "Allow",
                                "Action": ["tag:GetResources"],
                                "Resource": "*",
                            },
                        ],
                    }
                ),
                Tags=tags_as_kv,
            )

            policy_arn = response["Policy"]["Arn"]
            logger.debug(f"Role policy created: {policy_arn}")

            response = iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn=policy_arn
            )

        if create_console_network_policy:
            response = iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorNetworkAccess",
            )

        if enable_rds_policy:
            response = iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorRDSAccess",
            )

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

    logger.debug("Waiting 5 seconds before starting it (eventual consistency)")
    time.sleep(5)

    params = {"experimentTemplateId": experiment_template_id}
    if client_token:
        params["clientToken"] = client_token
    if tags:
        params["tags"] = scenario_tags

    try:
        return fis_client.start_experiment(**params)
    except Exception as ex:
        raise FailedActivity(f"Start Experiment failed, reason was: {ex}")


def restore_availability_zone_power_after_interruption(
    tags: Union[str, Dict[str, str], None] = None,
    delete_roles_and_policies: bool = True,
    delete_templates: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[AWSResponse]:
    """
    Restore Availability-Zone and clean any resources created for the experiment

    :param tags: str | Dict[str, str] | None representing tags to lookup
        experiments. When left empty, using a special tag key that was set
        on all resources during the start of the experiment
    :param delete_roles_and_policies: boolean, true means any created resources
        such as roles and policies will be deleted too
    :param delete_templates: boolean delete the template for the experiment
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon stopping the
        experiment
    """
    suffix = f"{threading.get_ident()}"

    if not tags:
        tags = {"chaostoolkit-experiment-key": suffix}

    logger.debug("Deleting experiment and restoring AZ")

    payload = stop_experiments_by_tags(
        tags=tags,
        delete_templates=delete_templates,
        configuration=configuration,
        secrets=secrets,
    )

    if delete_roles_and_policies:
        iam_client = aws_client(
            resource_name="iam", configuration=configuration, secrets=secrets
        )

        role_name = f"ChaosToolkit-FIS-{suffix}"
        logger.info(f"Deleting role {role_name}")

        try:
            response = iam_client.list_attached_role_policies(
                RoleName=role_name
            )
        except iam_client.exceptions.NoSuchEntityException:
            logger.debug("Failed to list attached role policies")

            try:
                response = iam_client.delete_role(RoleName=role_name)
            except iam_client.exceptions.NoSuchEntityException:
                logger.debug(f"Failed to delete role {role_name}")

            return payload

        logger.debug(f"Detaching policies {response}")

        policies = list(response["AttachedPolicies"])

        for policy in policies:
            logger.debug(f"Detaching policy {policy['PolicyName']}")
            try:
                iam_client.detach_role_policy(
                    RoleName=role_name, PolicyArn=policy["PolicyArn"]
                )
            except iam_client.exceptions.NoSuchEntityException:
                logger.debug(f"Failed to detach policy {policy['PolicyArn']}")
                continue

        try:
            response = iam_client.delete_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            logger.debug(f"Failed to delete role {role_name}")
            return payload

        for policy in policies:
            policy_name = policy["PolicyName"]
            # don't delete managed policies
            if policy_name in [
                "AWSFaultInjectionSimulatorRDSAccess",
                "AWSFaultInjectionSimulatorNetworkAccess",
                "AWSFaultInjectionSimulatorEC2Access",
            ]:
                continue

            logger.debug(f"Deleting policy {policy_name}")
            try:
                iam_client.delete_role_policy(
                    RoleName=role_name, PolicyName=policy_name
                )
            except iam_client.exceptions.NoSuchEntityException:
                logger.debug(f"Failed to delete policy {policy_name}")
                continue

    return payload
