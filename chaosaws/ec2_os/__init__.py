import os

from logzero import logger
from chaoslib.exceptions import FailedActivity

from .constants import OS_WINDOWS, OS_LINUX


def construct_script_content(action, os_type, parameters):

    cmd_param = ""
    if parameters is not None:
        cmd_param = '\n'.join(
            ['='.join([k, "'"+v+"'"]) for k, v in parameters.items()])
    else:
        logger.info("No parameter parsed, return default script content")

    if os_type == OS_WINDOWS:
        script_name = action+".ps1"
        # TODO in ps1
    elif os_type == OS_LINUX:
        script_name = action+".sh"
    else:
        raise FailedActivity(
            "Cannot find corresponding script for {} on OS: {}".format(
                action, os_type))

    with open(os.path.join(os.path.dirname(__file__),
                           "scripts", script_name)) as file:
        script_content = file.read()
    # merge duration
    script_content = cmd_param + "\n" + script_content
    return script_content
