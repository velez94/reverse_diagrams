import boto3
import argparse
import logging
from datetime import datetime
from aws.describe_organization import describe_organization, \
    list_accounts, index_accounts, list_roots, list_organizational_units, index_ous
from aws.describe_identity_store import order_accounts_assignments_list, extend_account_assignments, \
    list_permissions_set, list_groups, get_members, list_users, complete_group_members, add_users_and_groups_assign
from aws.describe_sso import list_instances, list_account_assignments, extends_permissions_set
from dgms.graph_mapper import create_mapper, create_sso_mapper_complete, create_sso_mapper


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
    parser.add_argument("-o", "--graph_organization",
                        help="Set if you want to create graph for your organization", action='store_true')
    parser.add_argument("-i", "--graph_identity",
                        help="Set if you want to create graph for your IAM Center", action='store_true')

    # Read arguments from command line
    args = parser.parse_args()
    logging.info(f"The arguments are {args}")

    if args.profile:
        profile = args.profile
        if profile is not None:
            boto3.setup_default_session(profile_name=profile)
        logging.info(f"Profile is: {profile}")

    if args.graph_organization:
        client_org = boto3.client('organizations')
        organization = describe_organization(client_org)
        print("The Organization info")
        print(organization)
        print("The Roots Info")
        roots = list_roots(client=client_org)
        print(roots)
        print("The Organizational Units list ")
        ous = list_organizational_units(parent_id=roots[0]["Id"], client=client_org)
        print(ous)
        print("The Organizational Units list with parents info")
        i_ous = index_ous(ous, client=client_org)
        print(i_ous)
        print("The Account list info")
        l_accounts = list_accounts(client_org)
        print(l_accounts)
        print("The Account list with parents info")
        i_accounts = index_accounts(l_accounts)
        print(i_accounts)

        create_mapper(template_file="graph_org.py", org=organization, root_id=roots[0]["Id"], list_ous=ous,
                      list_accounts=i_accounts)
    if args.graph_identity:
        # boto3.setup_default_session(profile_name='labvel-master', region_name="us-east-2")
        client_identity = boto3.client('identitystore', region_name="us-east-2")
        client_sso = boto3.client('sso-admin', region_name="us-east-2")

        store_instances = list_instances(client=client_sso)
        print(store_instances)
        store_id = store_instances[0]["IdentityStoreId"]
        store_arn = store_instances[0]["InstanceArn"]
        print("list groups")
        l_groups = list_groups(store_id, client=client_identity)
        print(l_groups)

        print("Get member group")

        m_groups = get_members(store_id, l_groups, client=client_identity)

        print(m_groups)

        print("Extend Group Members")
        l_users = list_users(store_id, client=client_identity)
        print(l_users)
        c_users_and_groups = complete_group_members(m_groups, l_users)

        print(c_users_and_groups)
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

        f_accounts= order_accounts_assignments_list(accounts_dict=l_accounts, account_assignments=account_assignments)
        create_sso_mapper_complete(template_file="graph_sso_complete.py", acc_assignments=f_accounts)
        create_sso_mapper(template_file="graph_sso.py", group_and_members= c_users_and_groups)


if __name__ == '__main__':
    main()
