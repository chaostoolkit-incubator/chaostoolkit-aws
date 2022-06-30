import os

from logzero import logger
from chaoslib.exceptions import FailedActivity

from .constants import OS_WINDOWS, OS_LINUX


def construct_script_content(action: str = None,
                             os_type: str = None,
                             parameters: dict = None):
    """
    As for now, no Windows action supported except burn CPU

    :param action:
    :param os_type: { OS_LINUX | OS_WINDOWS }
    :param parameters:
    :return:
    """

    cmd_param = ""
    if os_type == OS_LINUX:
        file_suffix = ".sh"
        p_delimiter = ""
        cmdline_delimiter = " && "
    elif os_type == OS_WINDOWS:
        file_suffix = ".ps1"
        p_delimiter = "$"
        cmdline_delimiter = "\n"
    else:
        raise FailedActivity(
            "Cannot find corresponding script for {} on OS: {}".format(
                action, os_type))

    if action == "run_cmd":
        cmdline_param = cmdline_delimiter.join(parameters['cmd'])
        # parameters.pop('cmd')
        del parameters['cmd']
    else:
        cmdline_param = ""

    if parameters is not None:
        param_list = list()
        for k, v in parameters.items():
            param_list.append('='.join([p_delimiter + k, "'" + v + "'"]))
        cmd_param = '\n'.join(param_list)
    else:
        logger.info("No parameter parsed, return default script content")

    script_name = action + file_suffix

    with open(os.path.join(os.path.dirname(__file__),
                           "scripts", script_name)) as file:
        script_content = file.read()
    # merge duration
    script_content = cmd_param + "\n" + cmdline_param + "\n" + script_content
    return script_content
