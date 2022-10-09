import boto3
import argparse
import logging
from datetime import datetime
from aws.describe_organization import describe_organization, list_accounts, index_accounts, get_ous


def main() -> int:
    """
    Validate SCP policies using AWS Access Analyzer API and create reports
    :return:
    """
    print('Compliance date:', datetime.now())

    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        help="AWS cli profile for Access Analyzer Api", default=None)
    parser.add_argument("-z", "--zip_reports",
                        help="Set in True if you want create a zip file for reports", default=False)

    # Read arguments from command line
    args = parser.parse_args()
    logging.info(f"The arguments are {args}")

    if args.profile:
        profile = args.profile
        if profile is not None:
            boto3.setup_default_session(profile_name=profile)
        logging.info(f"Profile is: {profile}")
    client = boto3.client('organizations')
    organization = describe_organization(client)
    print("The Organization info")
    print(organization)
    print("The Account list info")
    l_accounts=list_accounts(client)
    print(l_accounts)
    print("The Account list with parents info")
    i_accounts= index_accounts(l_accounts)
    print(i_accounts)
    print("The Organizational Units list ")
    l_ous= get_ous(i_accounts)
    print(l_ous[0], l_ous[1])


if __name__ == '__main__':
    main()
