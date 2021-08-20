from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

__all__ = ["get_experiment"]


def get_experiment(
    experiment_id: str, configuration: Configuration = None, secrets: Secrets = None
) -> AWSResponse:
    """
    Gets information about the specified experiment.

    :param experiment_id: str representing the id of the experiment to fetch information
        of
    :param configuration: Configuration object representing the CTK Configuration
    :param secrets: Secret object representing the CTK Secrets
    :returns: AWSResponse representing the response from FIS upon retrieving the
        experiment information

    Examples
    --------
    >>> get_experiment(
    ...    experiment_id="EXPTUCK2dxepXgkR38"
    ... )
    {'ResponseMetadata': {'RequestId': '0665fe39-2213-400b-b7ff-5f1ab9b7a5ea',
    'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Fri, 20 Aug 2021 11:08:27 GMT',
    ...
    'experiment': {'id': 'EXPTUCK2dxepXgkR38',
    'experimentTemplateId': 'EXT6oWVA1WrLNy4XS',
    ...
    }
    """

    if not experiment_id:
        raise FailedActivity(
            "You must pass a valid experiment id, id provided was empty"
        )

    fis_client = aws_client(
        resource_name="fis", configuration=configuration, secrets=secrets
    )

    try:
        return fis_client.get_experiment(id=experiment_id)
    except Exception as ex:
        raise FailedActivity(f"Get Experiment failed, reason was: {ex}")
