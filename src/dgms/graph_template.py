graph_template= """
from diagrams import Diagram, Cluster

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit

with Diagram("Organizations-State", show=False, direction="TB"):
    ou = OrganizationsOrganizationalUnit("OU")
    oa = OrganizationsAccount("Account")
"""
graph_template_sso= """
from diagrams import Diagram, Cluster

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit
from diagrams.aws.general import Users, User

with Diagram("SSO-State", show=False, direction="TB"):
    gg = Users("Group")
    uu= User("User")
"""

graph_template_sso_complete="""
from diagrams import Diagram, Cluster, Edge

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit
from diagrams.aws.general import Users, User
from diagrams.aws.security import IAMPermissions
with Diagram("IAM Identity Center", show=False, direction="LR"):
    gg = Users("Group")
    uu = User("User")
    pp= IAMPermissions("PermissionsSet")
    ou = OrganizationsOrganizationalUnit("PermissionsAssignments")
"""