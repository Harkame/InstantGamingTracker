import argparse

import logging

logger = logging.getLogger(__name__)


def get_arguments(arguments):
    argument_parser = argparse.ArgumentParser(
        description="Script to track product on Amazon",
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999),
    )

    argument_parser.add_argument(
        "-c",
        "--config_file",
        help="""Set config file
Example : python japscandownloader/main.py -c /home/myconfigfile.yml""",
        type=str,
    )

    argument_parser.add_argument(
        "-e",
        "--email",
        help="""Gmail address
Required with password option to send email
Example : python amazontracker/main.py -l mymailadress@gmail.com""",
        type=str,
    )

    argument_parser.add_argument(
        "-p",
        "--password",
        help="""Gmail password
Required with email option to send email
Example : python amazontracker/main.py -p mypassword""",
        type=str,
    )

    argument_parser.add_argument(
        "-n",
        "--notification",
        help="""SDK Admin Firebase private key
Example : python amazontracker/main.py -n /path/to/myprivatekey.json""",
        type=str,
    )

    argument_parser.add_argument(
        "-v",
        "--verbose",
        help="""Active verbose mode, support different level
Example : python japscandownloader/main.py -v""",
        action="count",
    )

    return argument_parser.parse_args(arguments)
