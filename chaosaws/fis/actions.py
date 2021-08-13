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
    """
    Starts running an experiment from the specified experiment template.

    :param experiment_template_id: str representing the id of the experiment template
        to run
    :param client_token: str representing the unique identifier for this experiment run.
        If a value is not provided, boto3 generates one for you
    :param tags: Dict[str, str] representing tags to apply to the experiment that is
        started
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon starting the
        experiment

    Examples
    --------
    >>> start_experiment(
    ...     experiment_template_id="EXT6oWVA1WrLNy4XS"
    ... )
    {
    'ResponseMetadata': {'RequestId': '1ceaedae-5897-4b64-9ade-9e94449f1262',
    'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Thu, 12 Aug 2021 14:21:19 GMT',
    ...
    'experiment': {'id': 'EXPXDPecuQBFiZs1Jz',
    'experimentTemplateId': 'EXT6oWVA1WrLNy4XS',
    ...
    }

    >>> start_experiment(
    ...     experiment_template_id="EXT6oWVA1WrLNy4XS",
    ...     client_token="my-unique-token",
    ...     tags={"a-key": "a-value"}
    ... )
    """

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
        raise FailedActivity(f"Start Experiment failed, reason was: {ex}")
