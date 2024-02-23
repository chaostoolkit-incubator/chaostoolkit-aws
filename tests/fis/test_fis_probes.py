from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.fis.probes import get_experiment


def test_that_fis_probe_modules___all___attribute_exposed_correctly():
    import chaosaws.fis.probes as probes

    all = probes.__all__
    assert "get_experiment" in all


@patch("chaosaws.fis.probes.aws_client", autospec=True)
def test_that_get_experiment_invoked_correctly_if_only_given_experiment_id(
    aws_client,
):
    client = MagicMock()
    aws_client.return_value = client

    get_experiment(experiment_id="an-id")
    client.get_experiment.assert_called_once_with(id="an-id")


@patch("chaosaws.fis.probes.aws_client", autospec=True)
def test_that_get_experiment_fails_if_experiment_id_empty_or_none(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    with pytest.raises(FailedActivity) as ex:
        get_experiment(experiment_id="")
    assert (
        str(ex.value)
        == "You must pass a valid experiment id, id provided was empty"
    )

    with pytest.raises(FailedActivity) as ex:
        get_experiment(experiment_id=None)
    assert (
        str(ex.value)
        == "You must pass a valid experiment id, id provided was empty"
    )


@patch("chaosaws.fis.probes.aws_client", autospec=True)
def test_that_get_experiment_fails_if_exception_raised(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.get_experiment.side_effect = Exception("Something went wrong")

    with pytest.raises(FailedActivity) as ex:
        get_experiment(experiment_id="an-id")
    assert (
        str(ex.value)
        == "Get Experiment failed, reason was: Something went wrong"
    )


@patch("chaosaws.fis.probes.aws_client", autospec=True)
def test_that_get_experiment_returns_client_response(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    resp = {"a-key", "a-value"}
    client.get_experiment.return_value = resp

    actual_resp = get_experiment(experiment_id="an-id")
    assert actual_resp == resp
