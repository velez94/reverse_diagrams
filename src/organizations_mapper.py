import boto3
import argparse
import logging
from datetime import datetime
from aws.describe_organization import describe_organization,\
    list_accounts, index_accounts, list_roots, list_organizational_units,index_ous
from dgms.graph_mapper import create_mapper


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
    print("The Roots Info")
    roots=list_roots(client=client)
    print(roots)
    print("The Organizational Units list ")
    ous=list_organizational_units(parent_id=roots[0]["Id"],client= client)
    print(ous)
    print("The Organizational Units list with parents info")
    i_ous= index_ous(ous,client=client)
    print(i_ous)
    print("The Account list info")
    l_accounts=list_accounts(client)
    print(l_accounts)
    print("The Account list with parents info")
    i_accounts= index_accounts(l_accounts)
    print(i_accounts)

    create_mapper(template_file="graph_org.py", org=organization, root_id=roots[0]["Id"], ous=ous, accounts=i_accounts)




if __name__ == '__main__':
    main()
