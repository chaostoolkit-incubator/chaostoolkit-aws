# -*- coding: utf-8 -*-
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["stop_task"]


def stop_task(cluster: str,
              task_id: str,
              reason: str = 'Chaos Testing',
              configuration: Configuration = None,
              secrets: Secrets = None) -> AWSResponse:
    """
    Stop a given ECS task instance
    """
    client = aws_client("ecs", configuration, secrets)
    return client.stop_task(cluster=cluster, task=task_id, reason=reason)
