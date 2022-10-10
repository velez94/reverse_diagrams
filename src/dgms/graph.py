
from diagrams import Diagram, Cluster

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit
from diagrams.aws.general import Users, User

with Diagram("Organizations-SSO-State", show=False, direction="LR"):
    ou = OrganizationsOrganizationalUnit("OU")
    oa = OrganizationsAccount("Account")
    gg = Users("Group")
    uu= User("User")

    with Cluster('Organizations'):

        oo = Organizations('o-9tlhkjyoii\n029921763173\nr-w3ow')

        ou_0= OrganizationsOrganizationalUnit("ou-w3ow-93hiq3zr")

        oo>> ou_0

        ou_1= OrganizationsOrganizationalUnit("ou-w3ow-5qsqi8b5")

        oo>> ou_1

        ou_2= OrganizationsOrganizationalUnit("ou-w3ow-w7dzhzcz")

        oo>> ou_2

        ou_3= OrganizationsOrganizationalUnit("ou-w3ow-k24p2opx")

        oo>> ou_3

        ou_0>> OrganizationsAccount("884478634998\nLog archive")

        ou_1>> OrganizationsAccount("582441254763\nProd")

        ou_0>> OrganizationsAccount("895882538541\nAudit")

        ou_2>> OrganizationsAccount("105171185823\nDevSecOps")

        ou_3>> OrganizationsAccount("994261317734\nLabVelCT")

        ou_2>> OrganizationsAccount("155794986228\nSharedServices")

        oo >> OrganizationsAccount("029921763173\nAlejandro Velez")

        ou_3>> OrganizationsAccount("571340586587\nDev")

    with Cluster('Groups'):

        gg_0= Users("AWSSecurityAuditors")

    with Cluster('Groups'):

        gg_1= Users("AWSLogArchiveAdmins")

    with Cluster('Groups'):

        gg_2= Users("DevSecOps_Admins")

        gg_2>> User("DevSecOpsAdm")

    with Cluster('Groups'):

        gg_3= Users("AWSLogArchiveViewers")

    with Cluster('Groups'):

        gg_4= Users("AWSSecurityAuditPowerUsers")

    with Cluster('Groups'):

        gg_5= Users("AWSAuditAccountAdmins")

    with Cluster('Groups'):

        gg_6= Users("AWSAccountFactory")

        gg_6>> User("velez94@protonmail.com")

    with Cluster('Groups'):

        gg_7= Users("AWSServiceCatalogAdmins")

    with Cluster('Groups'):

        gg_8= Users("AWSControlTowerAdmins")

        gg_8>> User("velez94@protonmail.com")
