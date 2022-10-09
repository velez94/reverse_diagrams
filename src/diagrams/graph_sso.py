
from diagrams import Diagram, Cluster

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit
from diagrams.aws.general import Users, User

with Diagram("SSO-State", show=False, direction="RL"):
    gg = Users("Group")
    uu= User("User")

    with Cluster('Groups'):

        gg_0= Users("AWSSecurityAuditors")

        gg_1= Users("AWSLogArchiveAdmins")

        with Cluster("DevSecOps_Admins"):

                gg_2= [User("DevSecOpsAdm"),]

        gg_3= Users("AWSLogArchiveViewers")

        gg_4= Users("AWSSecurityAuditPowerUsers")

        gg_5= Users("AWSAuditAccountAdmins")

        with Cluster("AWSAccountFactory"):

                gg_6= [User("velez94@protonmail.com"),]

        gg_7= Users("AWSServiceCatalogAdmins")

        with Cluster("AWSControlTowerAdmins"):

                gg_8= [User("velez94@protonmail.com"),]
