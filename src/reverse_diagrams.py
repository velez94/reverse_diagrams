"""Create graphs."""
import argparse
import logging

import argcomplete
from boto3 import setup_default_session

from .aws.describe_identity_store import graph_identity_center
from .aws.describe_organization import graph_organizations
from .banner.banner import get_version
from .version import __version__



def main() -> int:
    """
    Crete architecture diagram from your current state.

    :return:
    """
    # Initialize parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p", "--profile", help="AWS cli profile for AWS Apis", default=None
    )
    parser.add_argument(
        "-od",
        "--output_dir_path",
        help="Name of folder to save the diagrams python code files",
        default="diagrams",
    )
    parser.add_argument("-r", "--region", help="AWS region", default="us-east-2")
    parser.add_argument(
        "-o",
        "--graph_organization",
        help="Set if you want to create graph for your organization",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--graph_identity",
        help="Set if you want to create graph for your IAM Center",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--auto_create",
        help="Create Automatically diagrams",
        action="store_true",
        default=True,
    )
    parser.add_argument("-v", "--version", help="Show version", action="store_true")
    parser.add_argument("-d", "--debug", help="Debug Mode", action="store_true")

    # Read arguments from command line
    args = parser.parse_args()
    # Add autocomplete
    argcomplete.autocomplete(parser)
    logging.info(f"The arguments are {args}")
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    diagrams_path = args.output_dir_path

    region = args.region

    if args.profile:
        profile = args.profile
        if profile is not None:
            setup_default_session(profile_name=profile)

        logging.info(f"Profile is: {profile}")

    if args.graph_organization:
        graph_organizations(
            diagrams_path=diagrams_path, region=region, auto=args.auto_create
        )

    if args.graph_identity:
        graph_identity_center(
            diagrams_path=diagrams_path, region=region, auto=args.auto_create
        )

    if args.version:
        get_version(version=__version__)

    return 0


if __name__ == "__main__":
    main()
