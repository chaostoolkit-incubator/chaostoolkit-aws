# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaosaws.ecs.actions import stop_task


@patch('chaosaws.ecs.actions.aws_client', autospec=True)
def test_stop_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    cluster = "ecs-cluster"
    task_id = "16fd2706-8baf-433b-82eb-8c7fada847da"
    reason = "unit test"
    response = stop_task(cluster, task_id, reason)
    client.stop_task.assert_called_with(cluster=cluster, task=task_id, reason=reason)