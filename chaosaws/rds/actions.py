# -*- coding: utf-8 -*-
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse


def failover_db_cluster(db_cluster_identifier: str,
                        target_db_instance_identifier: str = None,
                        configuration: Configuration = None,
                        secrets: Secrets = None) -> AWSResponse:
    """
    Forces a failover for a DB cluster.
    """
    client = aws_client("rds", configuration, secrets)
    if not db_cluster_identifier:
        raise FailedActivity(
            "you must specify the db cluster identifier"
        )
    try:
        return client.failover_db_cluster(
            DBClusterIdentifier=db_cluster_identifier,
            TargetDBInstanceIdentifier=target_db_instance_identifier
        )
    except Exception as x:
        raise FailedActivity(
            "failed issuing a failover for DB cluster '{}': '{}'".format(
                db_cluster_identifier, str(x)))


def reboot_db_instance(db_instance_identifier: str,
                       force_failover: bool = False,
                       configuration: Configuration = None,
                       secrets: Secrets = None) -> AWSResponse:
    """
    Forces a reboot of your DB instance.
    """
    client = aws_client("rds", configuration, secrets)
    if not db_instance_identifier:
        raise FailedActivity(
            "you must specify the db instance identifier"
        )
    try:
        return client.reboot_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            ForceFailover=force_failover
        )
    except Exception as x:
        raise FailedActivity(
            "failed issuing a reboot of db instance '{}': '{}'".format(
                db_instance_identifier, str(x)))
