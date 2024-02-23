import json
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from chaoslib.exceptions import FailedActivity

from chaosaws.route53.probes import (
    get_dns_answer,
    get_health_check_status,
    get_hosted_zone,
)

module_path = os.path.dirname(os.path.abspath(__file__))


def read_in_data(filename):
    with open(os.path.join(module_path, "data", filename)) as fh:
        data = json.loads(fh.read())
    return data


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_hosted_zone(m_client):
    mock_response = read_in_data("get_hosted_zone_1.json")
    client = MagicMock()
    m_client.return_value = client
    client.get_hosted_zone.return_value = mock_response

    response = get_hosted_zone(zone_id="AAAAAAAAAAAAA")
    client.get_hosted_zone.assert_called_with(Id="AAAAAAAAAAAAA")
    assert response["HostedZone"]["Name"] == "aws.testrecord.com."


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_hosted_zone_not_found(m_client):
    mock_response = ClientError(
        operation_name="get_hosted_zone",
        error_response={
            "Error": {"Message": "Test Error", "Code": "NoSuchHostedZone"}
        },
    )
    client = MagicMock()
    m_client.return_value = client
    client.get_hosted_zone.side_effect = mock_response

    with pytest.raises(FailedActivity) as e:
        get_hosted_zone(zone_id="BBBBBBBBBBBBB")
    assert "Hosted Zone BBBBBBBBBBBBB not found." in str(e)


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_health_check_status(m_client):
    mock_response = read_in_data("get_health_check_status_1.json")
    client = MagicMock()
    m_client.return_value = client
    client.get_health_check_status.return_value = mock_response

    response = get_health_check_status(
        check_id="00000000-0000-0000-0000-000000000000"
    )

    client.get_health_check_status.assert_called_with(
        HealthCheckId="00000000-0000-0000-0000-000000000000"
    )
    assert len(response["HealthCheckObservations"]) == 2


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_health_check_status_not_found(m_client):
    mock_response = ClientError(
        operation_name="get_hosted_zone",
        error_response={
            "Error": {"Message": "Test Error", "Code": "NoSuchHealthCheck"}
        },
    )
    client = MagicMock()
    m_client.return_value = client
    client.get_health_check_status.side_effect = mock_response

    with pytest.raises(FailedActivity) as e:
        get_health_check_status(check_id="00000000-1111-1111-1111-000000000000")
    assert "Test Error" in str(e)


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_health_check_status_no_results(m_client):
    mock_response = {"HealthCheckObservations": []}
    client = MagicMock()
    m_client.return_value = client
    client.get_health_check_status.return_value = mock_response

    with pytest.raises(FailedActivity) as e:
        get_health_check_status(check_id="00000000-2222-2222-2222-000000000000")
    assert "No results found for" in str(e)


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_dns_answer(m_client):
    mock_response = read_in_data("test_dns_answer_1.json")
    client = MagicMock()
    m_client.return_value = client
    client.test_dns_answer.return_value = mock_response

    response = get_dns_answer(
        zone_id="AAAAAAAAAAAAA",
        record_name="aws.testrecord.com",
        record_type="A",
    )

    client.test_dns_answer.assert_called_with(
        HostedZoneId="AAAAAAAAAAAAA",
        RecordName="aws.testrecord.com",
        RecordType="A",
    )

    assert response["ResponseCode"] == "NOERROR"


@patch("chaosaws.route53.probes.aws_client", autospec=True)
def test_get_dns_answer_not_found(m_client):
    mock_response = ClientError(
        operation_name="get_hosted_zone",
        error_response={
            "Error": {"Message": "Test Error", "Code": "NoSuchHealthCheck"}
        },
    )
    client = MagicMock()
    m_client.return_value = client
    client.test_dns_answer.side_effect = mock_response

    with pytest.raises(FailedActivity) as e:
        get_dns_answer(
            zone_id="BBBBBBBBBBBBB",
            record_name="aws.testrecord.com",
            record_type="A",
        )
    assert "Test Error" in str(e)
