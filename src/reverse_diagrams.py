"""Create graphs."""
import argparse
import logging
import os

import argcomplete
import emoji
from boto3 import setup_default_session
from colorama import Fore

from .aws.describe_identity_store import (
    add_users_and_groups_assign,
    complete_group_members,
    extend_account_assignments,
    get_members,
    l_groups_to_d_groups,
    list_groups,
    list_users,
    order_accounts_assignments_list,
)
from .aws.describe_organization import (
    describe_organization,
    index_accounts,
    index_ous,
    list_accounts,
    list_organizational_units,
    list_roots,
)
from .aws.describe_sso import (
    extends_permissions_set,
    list_instances,
    list_permissions_set,
)
from .banner.banner import get_version
from .dgms.graph_mapper import (
    create_file,
    create_mapper,
    create_sso_mapper,
    create_sso_mapper_complete,
)
from .dgms.graph_template import (
    graph_template,
    graph_template_sso,
    graph_template_sso_complete,
)
from .reports.save_results import save_results
from .version import __version__


def graph_organizations(diagrams_path, region, auto):
    """
    Create organizations Graph.

    :param auto:
    :param diagrams_path:
    :param region:
    :return:
    """
    template_file = "graph_org.py"
    code_path = f"{diagrams_path}/code"
    json_path = f"{diagrams_path}/json"
    create_file(
        template_content=graph_template,
        file_name=template_file,
        directory_path=code_path,
    )

    organization = describe_organization(region=region)
    print(Fore.BLUE + emoji.emojize(":sparkle: Getting Organization Info" + Fore.RESET))
    logging.debug(organization)
    logging.debug("The Roots Info")
    roots = list_roots(region=region)
    logging.debug(roots)

    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Listing Organizational Units " + Fore.RESET)
    )
    logging.debug("The Organizational Units list ")
    ous = list_organizational_units(parent_id=roots[0]["Id"], region=region)
    logging.debug(ous)
    logging.debug("The Organizational Units list with parents info")
    i_ous = index_ous(ous, region=region)
    logging.debug(i_ous)

    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Getting the Account list info" + Fore.RESET)
    )
    l_accounts = list_accounts(region=region)
    logging.debug(l_accounts)
    logging.debug("The Account list with parents info")

    print(
        Fore.YELLOW
        + emoji.emojize(
            f":information:  There are {len(l_accounts)} Accounts in your organization"
            + Fore.RESET
        )
    )
    i_accounts = index_accounts(l_accounts, region=region)
    logging.debug(i_accounts)

    file_name = "organizations.json"
    save_results(results=i_accounts, filename=file_name, directory_path=json_path)

    create_mapper(
        template_file=f"{code_path}/{template_file}",
        org=organization,
        root_id=roots[0]["Id"],
        list_ous=ous,
        list_accounts=i_accounts,
    )
    if auto:
        print(f"{Fore.GREEN}❇️ Creating diagrams in {code_path}")
        command = os.system(f"cd {code_path} && python3 {template_file}")
        if command != 0:
            print(Fore.RED + "❌ Error creating diagrams")
            print(command)
    else:
        print(
            Fore.YELLOW
            + emoji.emojize(
                f":sparkles: Run -> python3 {code_path}/graph_org.py " + Fore.RESET
            )
        )


def graph_identity_center(diagrams_path, region, auto):
    """
    Create Identity center diagram.

    :param auto:
    :param diagrams_path:
    :param region:
    :return:
    """
    template_file = "graph_sso.py"
    template_file_complete = "graph_sso_complete.py"

    code_path = f"{diagrams_path}/code"
    json_path = f"{diagrams_path}/json"

    create_file(
        template_content=graph_template_sso,
        file_name=template_file,
        directory_path=code_path,
    )
    create_file(
        template_content=graph_template_sso_complete,
        file_name=template_file_complete,
        directory_path=code_path,
    )

    store_instances = list_instances(region=region)
    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Getting Identity store instance info" + Fore.RESET)
    )
    logging.debug(store_instances)
    store_id = store_instances[0]["IdentityStoreId"]
    store_arn = store_instances[0]["InstanceArn"]

    print(Fore.BLUE + emoji.emojize(":sparkle: List groups" + Fore.RESET))
    l_groups = list_groups(store_id, region=region)
    logging.debug(l_groups)
    print(
        Fore.YELLOW
        + emoji.emojize(
            f":information:  There are {len(l_groups)} Groups in your Identity Store"
            + Fore.RESET
        )
    )

    print(Fore.BLUE + emoji.emojize(":sparkle: Get groups and Users info" + Fore.RESET))
    m_groups = get_members(store_id, l_groups, region=region)
    logging.debug(m_groups)
    logging.debug("Extend Group Members")
    l_users = list_users(store_id, region=region)
    logging.debug(l_users)
    c_users_and_groups = complete_group_members(m_groups, l_users)
    d_groups = l_groups_to_d_groups(l_groups=c_users_and_groups)

    logging.debug(c_users_and_groups)
    # Get Account assignments
    permissions_set = list_permissions_set(instance_arn=store_arn, region=region)
    l_permissions_set_arn_name = extends_permissions_set(
        permissions_sets=permissions_set, store_arn=store_arn, region=region
    )

    l_accounts = list_accounts(region=region)
    account_assignments = extend_account_assignments(
        accounts_list=l_accounts,
        permissions_sets=l_permissions_set_arn_name,
        region=region,
        store_arn=store_arn,
    )

    account_assignments = add_users_and_groups_assign(
        account_assignments_list=account_assignments,
        user_and_group_list=c_users_and_groups,
        user_list=l_users,
        list_permissions_set_arn_name=l_permissions_set_arn_name,
    )

    print(
        Fore.BLUE
        + emoji.emojize(
            ":sparkle: Getting account assignments, users and groups" + Fore.RESET
        )
    )
    f_accounts = order_accounts_assignments_list(
        accounts_dict=l_accounts, account_assignments=account_assignments
    )
    f_path = os.path.join(code_path, template_file_complete)
    create_sso_mapper_complete(
        template_file=f_path, acc_assignments=f_accounts, d_groups=d_groups
    )

    save_results(
        results=f_accounts,
        filename="account_assignments.json",
        directory_path=json_path,
    )
    save_results(results=d_groups, filename="groups.json", directory_path=json_path)

    f_path = os.path.join(code_path, template_file)

    create_sso_mapper(template_file=f_path, group_and_members=c_users_and_groups)

    if auto:
        print(f"{Fore.GREEN}❇️ Creating diagrams in {code_path}")
        command_1 = os.system(f"cd {code_path} && python3 {template_file}")
        command = os.system(f"cd {code_path} && python3 {template_file_complete}")

        if command != 0 or command_1 != 0:
            print(Fore.RED + "❌ Error creating diagrams")
            print(command)
    else:
        print(
            Fore.YELLOW
            + emoji.emojize(
                f":sparkles:  Run -> python3 {code_path}/{template_file_complete}"
                f" or python3 {code_path}/{template_file}" + Fore.RESET
            )
        )


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
