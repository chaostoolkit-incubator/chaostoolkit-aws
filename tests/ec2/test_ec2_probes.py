# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from chaosaws.ec2.probes import describe_instances


@patch('chaosaws.ec2.probes.aws_client', autospec=True)
def test_describe_instances(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    filters = [{'Name': 'availability-zone', 'Values': ["us-west-1"]}]
    describe_instances(filters)
    client.describe_instances.assert_called_with(Filters=filters)
