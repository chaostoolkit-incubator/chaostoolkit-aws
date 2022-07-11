from datetime import datetime, timezone

import yaml
from chaoslib.types import Configuration, Experiment, Journal, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.s3.shared import validate_bucket_exists

__all__ = ["after_experiment_control"]


def after_experiment_control(
    bucket_name: str,
    dirpath: str,
    context: Experiment,
    state: Journal,
    as_yaml: bool = False,
    suffix_with_timestamp: bool = False,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> None:
    """
    Upload the journal of the run to an S3 bucket.

    ```json
    "{
        "controls": [
            {
                "name": "upload-results-to-s3",
                "provider": {
                    "type": "python",
                    "module": "chaosaws.s3.controls.upload",
                    "arguments": {
                        "bucket_name": "...",
                        "dirpath": "..."
                    }
                }
            }
        ]
    }
    ```

    You can indicate you want a timestamp suffix if you upload to the same
    directory all your results.

    """
    client = aws_client("s3", configuration=configuration, secrets=secrets)
    if not validate_bucket_exists(client, bucket_name):
        logger.error(
            f"Bucket '{bucket_name}' does not exist! Cannot upload the "
            "experiment's results"
        )
        return

    ext = "json"
    if as_yaml:
        ext = "yaml"
        state = yaml.safe_dump(state)
        context = yaml.safe_dump(context)

    if suffix_with_timestamp:
        ts = datetime.utcnow().replace(timezone=timezone.utc).isoformat()
        suffix = f"-{ts}"

    path = f"{dirpath}/journal{suffix}.{ext}"
    client.upload_fileobj(state, bucket_name, path)

    logger.debug(f"Results were uploaded to '{path}'")
