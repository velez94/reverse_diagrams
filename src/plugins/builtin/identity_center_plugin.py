"""AWS IAM Identity Center (SSO) plugin for generating identity and access diagrams."""
import logging
from typing import Dict, Any, List
from pathlib import Path

from src.plugins.base import AWSServicePlugin, PluginMetadata
from src.aws.client_manager import AWSClientManager
from src.models import DiagramConfig
from src.utils.concurrent import get_concurrent_processor
from src.utils.progress import get_progress_tracker

logger = logging.getLogger(__name__)


class IdentityCenterPlugin(AWSServicePlugin):
    """Plugin for AWS IAM Identity Center (SSO) diagram generation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="identity-center",
            version="1.0.0",
            description="Generate diagrams for AWS IAM Identity Center (SSO) groups, users, and permissions",
            author="Reverse Diagrams Team",
            aws_services=["sso-admin", "identitystore", "organizations"],
            dependencies=[]
        )
    
    def collect_data(self, client_manager: AWSClientManager, region: str, **kwargs) -> Dict[str, Any]:
        """
        Collect AWS IAM Identity Center data.
        
        Args:
            client_manager: AWS client manager
            region: AWS region
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing Identity Center data
        """
        logger.debug(f"Collecting AWS IAM Identity Center data from region {region}")
        progress = get_progress_tracker()
        
        data = {
            "region": region,
            "sso_instances": [],
            "identity_store_id": "",
            "instance_arn": "",
            "groups": [],
            "users": [],
            "group_memberships": [],
            "permission_sets": [],
            "permission_set_details": {},
            "account_assignments": [],
            "accounts": [],
            "final_account_assignments": {}
        }
        
        try:
            # Get SSO instances
            progress.show_success("🔐 Getting Identity Store Instance Info")
            instances_response = client_manager.call_api("sso-admin", "list_instances")
            data["sso_instances"] = instances_response.get("Instances", [])
            
            if not data["sso_instances"]:
                raise ValueError("No SSO instances found")
            
            data["identity_store_id"] = data["sso_instances"][0]["IdentityStoreId"]
            data["instance_arn"] = data["sso_instances"][0]["InstanceArn"]
            
            logger.debug(f"Using Identity Store ID: {data['identity_store_id']}")
            
            # Get groups
            progress.show_success("👥 Listing Groups")
            data["groups"] = self._list_groups(client_manager, data["identity_store_id"])
            logger.debug(f"Found {len(data['groups'])} groups")
            
            # Get users
            progress.show_success("👤 Listing Users")
            data["users"] = self._list_users(client_manager, data["identity_store_id"])
            logger.debug(f"Found {len(data['users'])} users")
            
            # Get group memberships
            progress.show_success("🔗 Getting Group Memberships")
            data["group_memberships"] = self._get_group_memberships(
                client_manager, data["identity_store_id"], data["groups"]
            )
            
            # Complete group members with user information
            data["group_memberships"] = self._complete_group_members(
                data["group_memberships"], data["users"]
            )
            
            # Get permission sets
            progress.show_success("🛡️ Listing Permission Sets")
            data["permission_sets"] = self._list_permission_sets(
                client_manager, data["instance_arn"]
            )
            logger.debug(f"Found {len(data['permission_sets'])} permission sets")
            
            # Get permission set details
            data["permission_set_details"] = self._get_permission_set_details(
                client_manager, data["instance_arn"], data["permission_sets"]
            )
            
            # Get organization accounts
            progress.show_success("🏢 Getting Organization Accounts")
            data["accounts"] = self._list_organization_accounts(client_manager)
            logger.debug(f"Found {len(data['accounts'])} accounts")
            
            # Get account assignments
            progress.show_success("📋 Getting Account Assignments")
            data["account_assignments"] = self._get_account_assignments(
                client_manager,
                data["instance_arn"],
                data["accounts"],
                data["permission_sets"]
            )
            
            # Add user and group information to assignments
            data["account_assignments"] = self._enrich_account_assignments(
                data["account_assignments"],
                data["group_memberships"],
                data["users"],
                data["permission_set_details"]
            )
            
            # Create final account assignments structure
            data["final_account_assignments"] = self._organize_account_assignments(
                data["accounts"], data["account_assignments"]
            )
            
            progress.show_summary(
                "Identity Center Summary",
                [
                    f"Identity Store ID: {data['identity_store_id']}",
                    f"Groups: {len(data['groups'])}",
                    f"Users: {len(data['users'])}",
                    f"Permission Sets: {len(data['permission_sets'])}",
                    f"Account Assignments: {len(data['account_assignments'])}"
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to collect Identity Center data: {e}")
            raise
        
        return data
    
    def _list_groups(self, client_manager: AWSClientManager, identity_store_id: str) -> List[Dict[str, Any]]:
        """List all groups in the identity store."""
        try:
            groups = client_manager.paginate_api_call(
                "identitystore",
                "list_groups",
                "Groups",
                IdentityStoreId=identity_store_id
            )
            return groups
        except Exception as e:
            logger.error(f"Failed to list groups: {e}")
            return []
    
    def _list_users(self, client_manager: AWSClientManager, identity_store_id: str) -> List[Dict[str, Any]]:
        """List all users in the identity store."""
        try:
            users = client_manager.paginate_api_call(
                "identitystore",
                "list_users",
                "Users",
                IdentityStoreId=identity_store_id
            )
            return users
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    def _get_group_memberships(
        self, 
        client_manager: AWSClientManager, 
        identity_store_id: str, 
        groups: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get group memberships for all groups."""
        group_memberships = []
        progress = get_progress_tracker()
        
        with progress.track_operation(f"Getting memberships for {len(groups)} groups", total=len(groups)) as task_id:
            for group in groups:
                try:
                    memberships = client_manager.paginate_api_call(
                        "identitystore",
                        "list_group_memberships",
                        "GroupMemberships",
                        IdentityStoreId=identity_store_id,
                        GroupId=group["GroupId"]
                    )
                    
                    group_memberships.append({
                        "group_id": group["GroupId"],
                        "group_name": group["DisplayName"],
                        "members": memberships
                    })
                    
                    progress.update_progress(task_id)
                    
                except Exception as e:
                    logger.warning(f"Failed to get memberships for group {group['GroupId']}: {e}")
                    group_memberships.append({
                        "group_id": group["GroupId"],
                        "group_name": group["DisplayName"],
                        "members": []
                    })
        
        return group_memberships
    
    def _complete_group_members(
        self, 
        group_memberships: List[Dict[str, Any]], 
        users: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Complete group member information with user details."""
        user_lookup = {user["UserId"]: user for user in users}
        
        for group_membership in group_memberships:
            for member in group_membership["members"]:
                user_id = member.get("MemberId", {}).get("UserId")
                if user_id and user_id in user_lookup:
                    user = user_lookup[user_id]
                    member["MemberId"]["UserName"] = user.get("UserName", "Unknown")
        
        return group_memberships
    
    def _list_permission_sets(self, client_manager: AWSClientManager, instance_arn: str) -> List[str]:
        """List all permission sets."""
        try:
            permission_sets = client_manager.paginate_api_call(
                "sso-admin",
                "list_permission_sets",
                "PermissionSets",
                InstanceArn=instance_arn
            )
            return permission_sets
        except Exception as e:
            logger.error(f"Failed to list permission sets: {e}")
            return []
    
    def _get_permission_set_details(
        self, 
        client_manager: AWSClientManager, 
        instance_arn: str, 
        permission_sets: List[str]
    ) -> Dict[str, str]:
        """Get detailed information for permission sets."""
        permission_set_details = {}
        progress = get_progress_tracker()
        
        with progress.track_operation(f"Getting details for {len(permission_sets)} permission sets", total=len(permission_sets)) as task_id:
            for permission_set_arn in permission_sets:
                try:
                    response = client_manager.call_api(
                        "sso-admin",
                        "describe_permission_set",
                        InstanceArn=instance_arn,
                        PermissionSetArn=permission_set_arn
                    )
                    
                    permission_set = response.get("PermissionSet", {})
                    permission_set_details[permission_set_arn] = permission_set.get("Name", "Unknown")
                    
                    progress.update_progress(task_id)
                    
                except Exception as e:
                    logger.warning(f"Failed to describe permission set {permission_set_arn}: {e}")
                    permission_set_details[permission_set_arn] = "Unknown"
        
        return permission_set_details
    
    def _list_organization_accounts(self, client_manager: AWSClientManager) -> List[Dict[str, Any]]:
        """List organization accounts."""
        try:
            accounts = client_manager.paginate_api_call(
                "organizations",
                "list_accounts",
                "Accounts"
            )
            return accounts
        except Exception as e:
            logger.warning(f"Failed to list organization accounts: {e}")
            return []
    
    def _get_account_assignments(
        self,
        client_manager: AWSClientManager,
        instance_arn: str,
        accounts: List[Dict[str, Any]],
        permission_sets: List[str]
    ) -> List[Dict[str, Any]]:
        """Get account assignments for all accounts and permission sets."""
        all_assignments = []
        progress = get_progress_tracker()
        
        total_operations = len(accounts) * len(permission_sets)
        
        with progress.track_operation(f"Getting account assignments", total=total_operations) as task_id:
            for account in accounts:
                for permission_set_arn in permission_sets:
                    try:
                        assignments = client_manager.paginate_api_call(
                            "sso-admin",
                            "list_account_assignments",
                            "AccountAssignments",
                            InstanceArn=instance_arn,
                            AccountId=account["Id"],
                            PermissionSetArn=permission_set_arn
                        )
                        
                        all_assignments.extend(assignments)
                        progress.update_progress(task_id)
                        
                    except Exception as e:
                        logger.debug(f"No assignments for account {account['Id']} and permission set {permission_set_arn}: {e}")
                        progress.update_progress(task_id)
        
        return all_assignments
    
    def _enrich_account_assignments(
        self,
        account_assignments: List[Dict[str, Any]],
        group_memberships: List[Dict[str, Any]],
        users: List[Dict[str, Any]],
        permission_set_details: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Add user and group information to account assignments."""
        # Create lookup dictionaries
        group_lookup = {group["group_id"]: group for group in group_memberships}
        user_lookup = {user["UserId"]: user for user in users}
        
        progress = get_progress_tracker()
        
        with progress.track_operation(f"Enriching {len(account_assignments)} assignments", total=len(account_assignments)) as task_id:
            for assignment in account_assignments:
                # Add permission set name
                permission_set_arn = assignment.get("PermissionSetArn", "")
                assignment["PermissionSetName"] = permission_set_details.get(permission_set_arn, "Unknown")
                
                # Add group or user information
                principal_type = assignment.get("PrincipalType", "")
                principal_id = assignment.get("PrincipalId", "")
                
                if principal_type == "GROUP" and principal_id in group_lookup:
                    assignment["GroupName"] = group_lookup[principal_id]["group_name"]
                elif principal_type == "USER" and principal_id in user_lookup:
                    assignment["UserName"] = user_lookup[principal_id].get("UserName", "Unknown")
                
                progress.update_progress(task_id)
        
        return account_assignments
    
    def _organize_account_assignments(
        self, 
        accounts: List[Dict[str, Any]], 
        account_assignments: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize account assignments by account name."""
        account_lookup = {account["Id"]: account["Name"] for account in accounts}
        organized_assignments = {}
        
        for assignment in account_assignments:
            account_id = assignment.get("AccountId", "")
            account_name = account_lookup.get(account_id, account_id)
            
            if account_name not in organized_assignments:
                organized_assignments[account_name] = []
            
            organized_assignments[account_name].append(assignment)
        
        return organized_assignments
    
    def generate_diagram_code(self, data: Dict[str, Any], config: DiagramConfig) -> str:
        """
        Generate diagram code for AWS IAM Identity Center.
        
        Args:
            data: Identity Center data collected from AWS
            config: Diagram configuration
            
        Returns:
            Python code for generating Identity Center diagram
        """
        logger.debug("Generating AWS IAM Identity Center diagram code")
        
        code_lines = [
            "from diagrams import Diagram, Cluster, Edge",
            "from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit",
            "from diagrams.aws.general import Users, User",
            "from diagrams.aws.security import IAMPermissions",
            "",
            f'with Diagram("{config.title}", show=False, direction="{config.direction}"):'
        ]
        
        # Get data
        final_assignments = data.get("final_account_assignments", {})
        group_memberships = data.get("group_memberships", [])
        
        # Create group lookup for members
        group_lookup = {group["group_name"]: group for group in group_memberships}
        
        # Generate account assignment clusters
        for account_name, assignments in final_assignments.items():
            if not assignments:
                continue
                
            code_lines.append(f"    with Cluster('Account: {account_name}'):")
            
            # Group assignments by group/user
            processed_principals = set()
            
            for assignment in assignments:
                principal_key = None
                
                if "GroupName" in assignment and assignment["GroupName"] not in processed_principals:
                    group_name = assignment["GroupName"]
                    principal_key = f"group_{self._format_name_for_code(group_name)}"
                    processed_principals.add(group_name)
                    
                    code_lines.append(f"        with Cluster('Group: {group_name}'):")
                    code_lines.append(f"            {principal_key} = Users(\"{self._split_long_name(group_name)}\")")
                    code_lines.append(f"            {principal_key} \\")
                    code_lines.append(f"                - Edge(color=\"brown\", style=\"dotted\", label=\"Permissions Set\") \\")
                    code_lines.append(f"                - IAMPermissions(\"{self._split_long_name(assignment['PermissionSetName'])}\")")
                    
                    # Add group members if available
                    if group_name in group_lookup:
                        members = group_lookup[group_name]["members"]
                        if members:
                            member_names = [m.get("MemberId", {}).get("UserName", "Unknown") for m in members]
                            members_code = self._create_users_list(member_names)
                            code_lines.append(f"            members_{self._format_name_for_code(group_name)} = {members_code}")
                            code_lines.append(f"            {principal_key} \\")
                            code_lines.append(f"                - Edge(color=\"darkgreen\", style=\"dotted\", label=\"Member\") \\")
                            code_lines.append(f"                - members_{self._format_name_for_code(group_name)}")
                
                elif "UserName" in assignment and assignment["UserName"] not in processed_principals:
                    user_name = assignment["UserName"]
                    principal_key = f"user_{self._format_name_for_code(user_name)}"
                    processed_principals.add(user_name)
                    
                    code_lines.append(f"        with Cluster('User: {user_name}'):")
                    code_lines.append(f"            {principal_key} = User(\"{self._split_long_name(user_name)}\")")
                    code_lines.append(f"            {principal_key} \\")
                    code_lines.append(f"                - Edge(color=\"brown\", style=\"dotted\") \\")
                    code_lines.append(f"                - IAMPermissions(\"{self._split_long_name(assignment['PermissionSetName'])}\")")
        
        return "\n".join(code_lines)
    
    def _format_name_for_code(self, name: str) -> str:
        """Format name for use in Python code."""
        import re
        # Remove special characters and spaces
        formatted = re.sub(r'[^\w]', '', name)
        return formatted if formatted else "Unknown"
    
    def _split_long_name(self, name: str) -> str:
        """Split long names for better display."""
        if len(name) > 17:
            return name[:16] + "\\n" + name[16:]
        return name
    
    def _create_users_list(self, user_names: List[str]) -> str:
        """Create a list of User objects for diagram code."""
        if not user_names:
            return "[]"
        
        user_objects = []
        for user_name in user_names[:5]:  # Limit to 5 users to avoid clutter
            user_objects.append(f'User("{self._split_long_name(user_name)}")')
        
        if len(user_names) > 5:
            user_objects.append(f'User("... and {len(user_names) - 5} more")')
        
        return "[" + ", ".join(user_objects) + "]"
    
    def get_required_permissions(self) -> List[str]:
        """Get required AWS permissions for Identity Center plugin."""
        return [
            "sso:ListInstances",
            "sso:ListPermissionSets",
            "sso:DescribePermissionSet",
            "sso:ListAccountAssignments",
            "identitystore:ListGroups",
            "identitystore:ListUsers",
            "identitystore:ListGroupMemberships",
            "organizations:ListAccounts"
        ]