import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.route53.actions import (
    associate_vpc_with_zone,
    disassociate_vpc_from_zone,
)

module_path = os.path.dirname(os.path.abspath(__file__))


def read_in_data(filename):
    with open(os.path.join(module_path, "data", filename)) as fh:
        data = json.loads(fh.read())
    return data


def mocked_client_error(op: str):
    return ClientError(
        operation_name=op,
        error_response={
            "Error": {"Message": "Test Error", "Code": "Test Error"}
        },
    )


@patch("chaosaws.route53.actions.aws_client", autospec=True)
def test_associate_vpc_with_zone(m_client):
    mock_response = read_in_data("associate_vpc_1.json")
    client = MagicMock()
    m_client.return_value = client
    client.associate_vpc_with_hosted_zone.return_value = mock_response

    response = associate_vpc_with_zone(
        zone_id="AAAAAAAAAAAAA",
        vpc_id="vpc-00000000",
        vpc_region="us-east-1",
        comment="CTK Associate",
    )

    client.associate_vpc_with_hosted_zone.assert_called_with(
        HostedZoneId="AAAAAAAAAAAAA",
        VPC={"VPCId": "vpc-00000000", "VPCRegion": "us-east-1"},
        Comment="CTK Associate",
    )

    assert response["ChangeInfo"]["Status"] == "Pending"


@patch("chaosaws.route53.actions.aws_client", autospec=True)
def test_associate_vpc_with_zone_exception(m_client):
    client = MagicMock()
    m_client.return_value = client
    client.associate_vpc_with_hosted_zone.side_effect = mocked_client_error(
        "associate_vpc_with_hosted_zone"
    )

    with pytest.raises(FailedActivity) as e:
        associate_vpc_with_zone(
            zone_id="1234567890123",
            vpc_id="vpc-00000000",
            vpc_region="us-east-1",
        )
    assert "Test Error" in str(e)


@patch("chaosaws.route53.actions.aws_client", autospec=True)
def test_disassociate_vpc_from_zone(m_client):
    mock_response = read_in_data("disassociate_vpc_1.json")
    client = MagicMock()
    m_client.return_value = client
    client.disassociate_vpc_from_hosted_zone.return_value = mock_response

    response = disassociate_vpc_from_zone(
        zone_id="AAAAAAAAAAAAA",
        vpc_id="vpc-00000000",
        vpc_region="us-east-1",
        comment="CTK Disassociate",
    )

    client.disassociate_vpc_from_hosted_zone.assert_called_with(
        HostedZoneId="AAAAAAAAAAAAA",
        VPC={"VPCId": "vpc-00000000", "VPCRegion": "us-east-1"},
        Comment="CTK Disassociate",
    )

    assert response["ChangeInfo"]["Status"] == "Pending"


@patch("chaosaws.route53.actions.aws_client", autospec=True)
def test_disassociate_vpc_with_zone_exception(m_client):
    client = MagicMock()
    m_client.return_value = client
    client.disassociate_vpc_from_hosted_zone.side_effect = mocked_client_error(
        "disassociate_vpc_from_hosted_zone"
    )

    with pytest.raises(FailedActivity) as e:
        disassociate_vpc_from_zone(
            zone_id="1234567890123",
            vpc_id="vpc-00000000",
            vpc_region="us-east-1",
        )
    assert "Test Error" in str(e)
