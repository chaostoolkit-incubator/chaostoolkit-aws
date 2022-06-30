import boto3
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = [
    "failover_db_cluster",
    "reboot_db_instance",
    "stop_db_instance",
    "stop_db_cluster",
    "delete_db_instance",
    "delete_db_cluster",
    "delete_db_cluster_endpoint",
]


def failover_db_cluster(
    db_cluster_identifier: str,
    target_db_instance_identifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Forces a failover for a DB cluster.
    """
    client = aws_client("rds", configuration, secrets)
    if not db_cluster_identifier:
        raise FailedActivity("you must specify the db cluster identifier")
    try:
        return client.failover_db_cluster(
            DBClusterIdentifier=db_cluster_identifier,
            TargetDBInstanceIdentifier=target_db_instance_identifier,
        )
    except Exception as x:
        raise FailedActivity(
            "failed issuing a failover for DB cluster '{}': '{}'".format(
                db_cluster_identifier, str(x)
            )
        )


def reboot_db_instance(
    db_instance_identifier: str,
    force_failover: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Forces a reboot of your DB instance.
    """
    client = aws_client("rds", configuration, secrets)
    if not db_instance_identifier:
        raise FailedActivity("you must specify the db instance identifier")
    try:
        return client.reboot_db_instance(
            DBInstanceIdentifier=db_instance_identifier, ForceFailover=force_failover
        )
    except Exception as x:
        raise FailedActivity(
            "failed issuing a reboot of db instance '{}': '{}'".format(
                db_instance_identifier, str(x)
            )
        )


def stop_db_instance(
    db_instance_identifier: str,
    db_snapshot_identifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Stops a RDS DB instance

    - db_instance_identifier: the instance identifier of the RDS instance
    - db_snapshot_identifier: the name of the DB snapshot made before stop
    """
    client = aws_client("rds", configuration, secrets)

    params = dict(DBInstanceIdentifier=db_instance_identifier)
    if db_snapshot_identifier:
        params["DBSnapshotIdentifier"] = db_snapshot_identifier

    try:
        return client.stop_db_instance(**params)
    except ClientError as e:
        raise FailedActivity(
            "Failed to stop RDS DB instance %s: %s"
            % (db_instance_identifier, e.response["Error"]["Message"])
        )


def stop_db_cluster(
    db_cluster_identifier: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Stop a RDS Cluster

    - db_cluster_identifier: the identifier of the RDS cluster to stop
    """
    client = aws_client("rds", configuration, secrets)

    try:
        return client.stop_db_cluster(DBClusterIdentifier=db_cluster_identifier)
    except ClientError as e:
        raise FailedActivity(
            "Failed to stop RDS DB Cluster %s: %s"
            % (db_cluster_identifier, e.response["Error"]["Message"])
        )


def delete_db_instance(
    db_instance_identifier: str,
    skip_final_snapshot: bool = True,
    db_snapshot_identifier: str = None,
    delete_automated_backups: bool = True,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Deletes a RDS instance

    - db_instance_identifier: the identifier of the RDS instance to delete
    - skip_final_snapshot: boolean (true): determines whether or not to
        perform a final snapshot of the rds instance before deletion
    - db_snapshot_identifier: the identifier to give the final rds snapshot
    - delete_automated_backups: boolean (true): determines if the automated
        backups of the rds instance are deleted immediately
    """
    client = aws_client("rds", configuration, secrets)

    params = dict(
        DBInstanceIdentifier=db_instance_identifier,
        DeleteAutomatedBackups=delete_automated_backups,
        SkipFinalSnapshot=skip_final_snapshot,
    )

    if not skip_final_snapshot:
        if not db_snapshot_identifier:
            raise FailedActivity(
                "You must provide a snapshot identifier if "
                "taking a final DB snapshot"
            )
        params["FinalDBSnapshotIdentifier"] = db_snapshot_identifier

    try:
        return client.delete_db_instance(**params)
    except ClientError as e:
        raise FailedActivity(
            "Failed to delete RDS DB instance %s: %s"
            % (db_instance_identifier, e.response["Error"]["Message"])
        )


def delete_db_cluster(
    db_cluster_identifier: str,
    skip_final_snapshot: bool = True,
    db_snapshot_identifier: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Deletes an Aurora DB cluster

    - db_cluster_identifier: the identifier of the cluster to delete
    - skip_final_snapshot: boolean (true): determines whether or not to
        perform a final snapshot of the cluster before deletion
    - db_snapshot_identifier: the identifier to give the final rds snapshot
    """
    client = aws_client("rds", configuration, secrets)

    params = dict(
        DBClusterIdentifier=db_cluster_identifier, SkipFinalSnapshot=skip_final_snapshot
    )

    if not skip_final_snapshot:
        if not db_snapshot_identifier:
            raise FailedActivity(
                "You must provide a snapshot identifier if "
                "taking a final DB snapshot"
            )
        params["FinalDBSnapshotIdentifier"] = db_snapshot_identifier

    try:
        return client.delete_db_cluster(**params)
    except ClientError as e:
        raise FailedActivity(
            "Failed to delete RDS DB cluster %s: %s"
            % (db_cluster_identifier, e.response["Error"]["Message"])
        )


def delete_db_cluster_endpoint(
    db_cluster_identifier: str,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:
    """
    Deletes the custom endpoint of an Aurora cluster

    - db_cluster_identifier: the identifier of the cluster to delete the
        endpoint from
    """
    client = aws_client("rds", configuration, secrets)
    cluster = describe_db_cluster(db_cluster_identifier, client)

    try:
        return client.delete_db_cluster_endpoint(
            DBClusterEndpointIdentifier=cluster["Endpoint"]
        )
    except ClientError as e:
        raise FailedActivity(
            "unable to delete endpoint for cluster %s: %s"
            % (db_cluster_identifier, e.response["Error"]["Message"])
        )


###############################################################################
# Private functions
###############################################################################
def describe_db_cluster(cluster_id: str, client: boto3.client) -> AWSResponse:
    try:
        return client.describe_db_clusters(DBClusterIdentifier=cluster_id)[
            "DBClusters"
        ][0]
    except ClientError as e:
        raise FailedActivity(
            "unable to identify cluster %s: %s"
            % (cluster_id, e.response["Error"]["Message"])
        )
