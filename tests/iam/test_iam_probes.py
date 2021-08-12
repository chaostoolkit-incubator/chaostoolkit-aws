from unittest.mock import MagicMock, patch

from chaosaws.iam.probes import get_policy


@patch("chaosaws.iam.probes.aws_client", autospec=True)
def test_get_role_policy(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    arn = "aws:iam:whatever"
    get_policy(arn)
    client.get_policy.assert_called_with(PolicyArn=arn)
