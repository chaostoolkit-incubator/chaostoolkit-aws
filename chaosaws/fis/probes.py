from chaoslib.types import Configuration, Secrets

from chaosaws.types import AWSResponse


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
    pass
