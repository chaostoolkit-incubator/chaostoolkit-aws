from unittest.mock import MagicMock, patch

import pytest
from chaoslib.exceptions import FailedActivity

from chaosaws.fis.actions import (
    start_experiment,
    stop_experiment,
    stop_experiments_by_tags,
)


def test_that_fis_action_modules___all___attribute_exposed_correctly():
    import chaosaws.fis.actions as actions

    all = actions.__all__
    assert "start_experiment" in all
    assert "stop_experiment" in all


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_start_experiment_invoked_correctly_if_only_given_template_id(
    aws_client,
):
    client = MagicMock()
    aws_client.return_value = client

    start_experiment(experiment_template_id="an-id")
    client.start_experiment.assert_called_once_with(
        experimentTemplateId="an-id"
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_start_experiment_invoked_correctly_if_given_all_params(
    aws_client,
):
    client = MagicMock()
    aws_client.return_value = client

    start_experiment(
        experiment_template_id="an-id",
        client_token="a-token",
        tags={"test-tag": "a-value"},
    )
    client.start_experiment.assert_called_once_with(
        experimentTemplateId="an-id",
        clientToken="a-token",
        tags={"test-tag": "a-value"},
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_start_experiment_fails_if_template_id_empty_or_none(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    with pytest.raises(FailedActivity) as ex:
        start_experiment(experiment_template_id="")
    assert str(ex.value) == (
        "You must pass a valid experiment template id, id provided was empty"
    )

    with pytest.raises(FailedActivity) as ex:
        start_experiment(experiment_template_id=None)
    assert str(ex.value) == (
        "You must pass a valid experiment template id, id provided was empty"
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_start_experiment_fails_if_exception_raised(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.start_experiment.side_effect = Exception("Something went wrong")

    with pytest.raises(FailedActivity) as ex:
        start_experiment(experiment_template_id="an-id")
    assert (
        str(ex.value)
        == "Start Experiment failed, reason was: Something went wrong"
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_start_experiment_returns_client_response(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    resp = {"a-key": "a-value"}
    client.start_experiment.return_value = resp

    actual_resp = start_experiment(experiment_template_id="an-id")
    assert actual_resp == resp


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_stop_experiment_invoked_correctly_when_given_experiment_id(
    aws_client,
):
    client = MagicMock()
    aws_client.return_value = client

    stop_experiment(experiment_id="an-id")
    client.stop_experiment.assert_called_once_with(id="an-id")


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_stop_experiment_fails_if_experiment_id_empty_or_none(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    with pytest.raises(FailedActivity) as ex:
        stop_experiment(experiment_id="")
    assert str(ex.value) == (
        "You must pass a valid experiment id, id provided was empty"
    )

    with pytest.raises(FailedActivity) as ex:
        stop_experiment(experiment_id=None)
    assert str(ex.value) == (
        "You must pass a valid experiment id, id provided was empty"
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_stop_experiment_fails_if_exception_raised(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    client.stop_experiment.side_effect = Exception("Something went wrong")

    with pytest.raises(FailedActivity) as ex:
        stop_experiment(experiment_id="an-id")
    assert (
        str(ex.value)
        == "Stop Experiment failed, reason was: Something went wrong"
    )


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_stop_experiment_returns_client_response(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    resp = {"a-key": "a-value"}
    client.stop_experiment.return_value = resp

    actual_resp = stop_experiment(experiment_id="an-id")
    assert actual_resp == resp


@patch("chaosaws.fis.actions.aws_client", autospec=True)
def test_that_stop_experiment_by_tags(aws_client):
    client = MagicMock()
    aws_client.return_value = client

    resp = {
        "experiments": [
            {
                "id": "an-id",
                "experimentTemplateId": "template-id",
                "tags": {"test-tag": "a-value"},
                "state": {"status": "running"},
            }
        ]
    }
    client.list_experiments.return_value = resp

    stop_experiments_by_tags(tags={"test-tag": "a-value"})
    client.stop_experiment.assert_called_once_with(id="an-id")
