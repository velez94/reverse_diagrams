import boto3
import argparse
import logging
from colorama import Fore
from datetime import datetime
from .aws.describe_organization import describe_organization, \
    list_accounts, index_accounts, list_roots, list_organizational_units, index_ous
from .aws.describe_identity_store import order_accounts_assignments_list, extend_account_assignments, \
    list_groups, get_members, list_users, complete_group_members, add_users_and_groups_assign
from .aws.describe_sso import list_instances, extends_permissions_set, list_permissions_set
from .dgms.graph_mapper import create_mapper, create_sso_mapper_complete, create_sso_mapper, create_file
from .dgms.graph_template import graph_template, graph_template_sso, graph_template_sso_complete
from .banner.banner import get_version

__version__ = "0.1.7"


def main() -> int:
    """
    Crete architecture diagram from your current state
    :return:
    """
    print('Date:', datetime.now())

    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cloud",
                        help="Cloud Provider, aws, gcp, azure", default="aws")
    parser.add_argument("-p", "--profile",
                        help="AWS cli profile for Access Analyzer Api", default=None)
    parser.add_argument("-r", "--region",
                        help="AWS cli profile for Access Analyzer Api", default="us-east-2")
    parser.add_argument("-o", "--graph_organization",
                        help="Set if you want to create graph for your organization", action='store_true')
    parser.add_argument("-i", "--graph_identity",
                        help="Set if you want to create graph for your IAM Center", action='store_true')
    parser.add_argument("-v", "--version",
                        help="Show version", action='store_true')
    parser.add_argument("-d", "--debug",
                        help="Debug Mode", action='store_true')

    # Read arguments from command line
    args = parser.parse_args()
    logging.info(f"The arguments are {args}")
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.cloud == "aws":
        if args.profile:
            profile = args.profile
            if profile is not None:
                boto3.setup_default_session(profile_name=profile)

            logging.info(f"Profile is: {profile}")
        if args.region:
            region = args.region

        if args.graph_organization:
            create_file(template_content=graph_template, file_name="graph_org.py")

            client_org = boto3.client('organizations')
            organization = describe_organization(client_org)
            print(Fore.BLUE + "🔄 Getting Organization Info" + Fore.RESET)
            logging.debug(organization)
            logging.debug("The Roots Info")
            roots = list_roots(client=client_org)
            logging.debug(roots)
            print(Fore.BLUE + "🔄 The Organizational Units list " + Fore.RESET)
            logging.debug("The Organizational Units list ")
            ous = list_organizational_units(parent_id=roots[0]["Id"], client=client_org)
            logging.debug(ous)
            logging.debug("The Organizational Units list with parents info")
            i_ous = index_ous(ous, client=client_org)
            logging.debug(i_ous)
            print(Fore.BLUE + "🔄 Getting the Account list info" + Fore.RESET)
            l_accounts = list_accounts(client_org)
            logging.debug(l_accounts)
            logging.debug("The Account list with parents info")
            i_accounts = index_accounts(l_accounts)
            logging.debug(i_accounts)

            create_mapper(template_file="graph_org.py", org=organization, root_id=roots[0]["Id"], list_ous=ous,
                          list_accounts=i_accounts)

            print(Fore.YELLOW + "Run -> python3 graph_org.py " + Fore.RESET)

        if args.graph_identity:
            create_file(template_content=graph_template_sso, file_name="graph_sso.py")
            create_file(template_content=graph_template_sso_complete, file_name="graph_sso_complete.py")

            client_identity = boto3.client('identitystore', region_name=region)
            client_sso = boto3.client('sso-admin', region_name=region)

            store_instances = list_instances(client=client_sso)
            print(Fore.BLUE + "🔄 Getting Identity store instance info" + Fore.RESET)
            logging.debug(store_instances)
            store_id = store_instances[0]["IdentityStoreId"]
            store_arn = store_instances[0]["InstanceArn"]
            print(Fore.BLUE + "List groups" + Fore.RESET)
            l_groups = list_groups(store_id, client=client_identity)
            logging.debug(l_groups)

            print(Fore.BLUE + "🔄Get groups and Users info" + Fore.RESET)

            m_groups = get_members(store_id, l_groups, client=client_identity)

            logging.debug(m_groups)

            logging.debug("Extend Group Members")
            l_users = list_users(store_id, client=client_identity)
            logging.debug(l_users)
            c_users_and_groups = complete_group_members(m_groups, l_users)

            logging.debug(c_users_and_groups)
            # Get Account assingments
            permissions_set = list_permissions_set(instance_arn=store_arn, client=client_sso)
            l_permissions_set_arn_name = extends_permissions_set(permissions_sets=permissions_set, store_arn=store_arn,
                                                                 client_sso=client_sso)

            client_org = boto3.client('organizations')
            l_accounts = list_accounts(client_org)
            account_assignments = extend_account_assignments(accounts_list=l_accounts,
                                                             permissions_sets=l_permissions_set_arn_name,
                                                             client_sso=client_sso,
                                                             store_arn=store_arn)

            account_assignments = add_users_and_groups_assign(account_assignments_list=account_assignments,
                                                              user_and_group_list=c_users_and_groups,
                                                              user_list=l_users,
                                                              list_permissions_set_arn_name=l_permissions_set_arn_name)
            print(Fore.BLUE + "🔄 Getting account assignments, users and groups" + Fore.RESET)
            f_accounts = order_accounts_assignments_list(accounts_dict=l_accounts,
                                                         account_assignments=account_assignments)
            create_sso_mapper_complete(template_file="graph_sso_complete.py", acc_assignments=f_accounts)
            create_sso_mapper(template_file="graph_sso.py", group_and_members=c_users_and_groups)
            print(Fore.YELLOW + "Run -> python3 graph_sso_complete.py " + Fore.RESET)
    else:
        print(Fore.RED + f"The cloud provider {args.cloud} is no available" + Fore.RESET)
    if args.version:
        get_version(version=__version__)

    return 0


if __name__ == '__main__':
    main()
