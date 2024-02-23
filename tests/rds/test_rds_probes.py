import json
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.rds.probes import (
    cluster_membership_count,
    cluster_status,
    instance_status,
)


class TestRDSProbes(TestCase):
    def setUp(self) -> None:
        data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "rds_data.json"
        )
        with open(data_file) as fh:
            self.test_data = json.loads(fh.read())

    @patch("chaosaws.rds.probes.aws_client", autospec=True)
    def test_get_instance_status_instance_id(self, aws_client):
        instance_id = "MyTestInstanceRDS"
        client = MagicMock()
        aws_client.return_value = client
        client.get_paginator.return_value.paginate.return_value = (
            self.test_data["instances"]["single"]
        )

        response = instance_status(instance_id=instance_id)
        client.get_paginator.return_value.paginate.assert_called_with(
            DBInstanceIdentifier=instance_id
        )
        self.assertEqual(response, "available")

    @patch("chaosaws.rds.probes.aws_client", autospec=True)
    def test_get_instance_status_filters(self, aws_client):
        client = MagicMock()
        aws_client.return_value = client
        client.get_paginator.return_value.paginate.return_value = (
            self.test_data["instances"]["multiple"]
        )

        filters = [{"Name": "engine", "Values": ["mysql"]}]
        response = instance_status(filters=filters)
        client.get_paginator.return_value.paginate.assert_called_with(
            Filters=filters
        )
        self.assertEqual(response, "available")

    def test_get_instance_status_no_parameters(self):
        with pytest.raises(FailedActivity) as x:
            instance_status()
        self.assertIn("instance_id or filters are required", str(x))

    @patch("chaosaws.rds.probes.aws_client", autospec=True)
    def test_get_cluster_status_cluster_id(self, aws_client):
        cluster_id = "MyTestClusterRDS"
        client = MagicMock()
        aws_client.return_value = client
        client.get_paginator.return_value.paginate.return_value = (
            self.test_data["clusters"]["single"]
        )

        response = cluster_status(cluster_id=cluster_id)
        client.get_paginator.return_value.paginate.assert_called_with(
            DBClusterIdentifier=cluster_id
        )
        self.assertEqual(response, "available")

    @patch("chaosaws.rds.probes.aws_client", autospec=True)
    def test_get_cluster_status_filters(self, aws_client):
        client = MagicMock()
        aws_client.return_value = client
        client.get_paginator.return_value.paginate.return_value = (
            self.test_data["clusters"]["multiple"]
        )

        filters = [{"Name": "engine", "Values": ["mysql"]}]
        response = cluster_status(filters=filters)
        client.get_paginator.return_value.paginate.assert_called_with(
            Filters=filters
        )
        self.assertEqual(response, "available")

    @patch("chaosaws.rds.probes.aws_client", autospec=True)
    def test_get_cluster_membership_count(self, aws_client):
        cluster_id = "MyTestClusterRDS"
        client = MagicMock()
        aws_client.return_value = client
        client.get_paginator.return_value.paginate.return_value = (
            self.test_data["clusters"]["single"]
        )

        response = cluster_membership_count(cluster_id=cluster_id)
        client.get_paginator.return_value.paginate.assert_called_with(
            DBClusterIdentifier=cluster_id
        )
        self.assertEqual(response, 3)

    def test_get_cluster_status_no_parameters(self):
        with pytest.raises(FailedActivity) as x:
            cluster_status()
        self.assertIn("cluster_id or filters are required", str(x))
