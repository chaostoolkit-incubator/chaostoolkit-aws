from typing import Dict

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse


__all__ = ["start_experiment"]


def start_experiment(
    experiment_template_id: str,
    client_token: str = None,
    tags: Dict[str, str] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> AWSResponse:

    if not experiment_template_id:
        raise FailedActivity(
            "You must pass a valid experiment template id, id provided was empty"
        )

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    params = {"experimentTemplateId": experiment_template_id}
    if client_token:
        params["clientToken"] = client_token
    if tags:
        params["tags"] = tags

    try:
        return fis_client.start_experiment(**params)
    except Exception as ex:
        raise FailedActivity(
            f"Start Experiment failed, reason was: {ex}"
        )
