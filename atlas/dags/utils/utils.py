import logging
import shlex
import subprocess

from io import StringIO


def run_shell_command(command_line):
    command_line_args = shlex.split(command_line)
    logging.info('Subprocess: "' + command_line + '"')
    try:
        command_line_process = subprocess.Popen(
            command_line_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        process_output, _ = command_line_process.communicate()
        for line in process_output.decode("utf-8").split("\n"):
            logging.info(line)
        process_output = StringIO(process_output.decode("utf-8"))
    except Exception as exc:
        logging.info("Exception occurred: " + str(exc))
        logging.info("Subprocess failed")
        return False
    else:
        # no exception was raised
        logging.info("Subprocess finished")
    return True


def regional_config(atlas_region):
    return "regional_config_{atlas_region}".format(atlas_region=atlas_region)


def pbf_filename(atlas_region, regional_cfg):
    return "{atlas_region}-{atlas_region_timestamp}.osm.pbf".format(
        atlas_region=atlas_region,
        atlas_region_timestamp=regional_cfg["download_pbf_timestamp"],
    )
