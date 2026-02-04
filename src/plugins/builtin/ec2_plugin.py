"""EC2 service plugin for generating EC2 infrastructure diagrams."""
import logging
from typing import Dict, Any, List

from src.plugins.base import AWSServicePlugin, PluginMetadata
from src.aws.client_manager import AWSClientManager
from src.models import DiagramConfig
from src.utils.concurrent import get_concurrent_processor

logger = logging.getLogger(__name__)


class EC2Plugin(AWSServicePlugin):
    """Plugin for AWS EC2 service diagram generation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="ec2",
            version="1.0.0",
            description="Generate diagrams for EC2 instances, VPCs, and related resources",
            author="Reverse Diagrams Team",
            aws_services=["ec2"],
            dependencies=[]
        )
    
    def collect_data(self, client_manager: AWSClientManager, region: str, **kwargs) -> Dict[str, Any]:
        """
        Collect EC2 data from AWS.
        
        Args:
            client_manager: AWS client manager
            region: AWS region
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing EC2 data
        """
        logger.debug(f"Collecting EC2 data from region {region}")
        
        data = {
            "region": region,
            "vpcs": [],
            "instances": [],
            "security_groups": [],
            "subnets": [],
            "internet_gateways": [],
            "route_tables": []
        }
        
        try:
            # Collect VPCs
            vpcs_response = client_manager.call_api("ec2", "describe_vpcs")
            data["vpcs"] = vpcs_response.get("Vpcs", [])
            logger.debug(f"Found {len(data['vpcs'])} VPCs")
            
            # Collect EC2 instances
            instances_response = client_manager.call_api("ec2", "describe_instances")
            instances = []
            for reservation in instances_response.get("Reservations", []):
                instances.extend(reservation.get("Instances", []))
            data["instances"] = instances
            logger.debug(f"Found {len(data['instances'])} EC2 instances")
            
            # Collect Security Groups
            sg_response = client_manager.call_api("ec2", "describe_security_groups")
            data["security_groups"] = sg_response.get("SecurityGroups", [])
            logger.debug(f"Found {len(data['security_groups'])} security groups")
            
            # Collect Subnets
            subnets_response = client_manager.call_api("ec2", "describe_subnets")
            data["subnets"] = subnets_response.get("Subnets", [])
            logger.debug(f"Found {len(data['subnets'])} subnets")
            
            # Collect Internet Gateways
            igw_response = client_manager.call_api("ec2", "describe_internet_gateways")
            data["internet_gateways"] = igw_response.get("InternetGateways", [])
            logger.debug(f"Found {len(data['internet_gateways'])} internet gateways")
            
            # Collect Route Tables
            rt_response = client_manager.call_api("ec2", "describe_route_tables")
            data["route_tables"] = rt_response.get("RouteTables", [])
            logger.debug(f"Found {len(data['route_tables'])} route tables")
            
        except Exception as e:
            logger.error(f"Failed to collect EC2 data: {e}")
            raise
        
        return data
    
    def generate_diagram_code(self, data: Dict[str, Any], config: DiagramConfig) -> str:
        """
        Generate diagram code for EC2 resources.
        
        Args:
            data: EC2 data collected from AWS
            config: Diagram configuration
            
        Returns:
            Python code for generating EC2 diagram
        """
        logger.debug("Generating EC2 diagram code")
        
        code_lines = [
            "from diagrams import Diagram, Cluster, Edge",
            "from diagrams.aws.compute import EC2",
            "from diagrams.aws.network import VPC, PrivateSubnet, PublicSubnet, InternetGateway, RouteTable",
            "from diagrams.aws.security import SecurityGroup",
            "",
            f'with Diagram("{config.title}", show=False, direction="{config.direction}"):'
        ]
        
        # Group instances by VPC
        vpc_instances = {}
        for instance in data.get("instances", []):
            vpc_id = instance.get("VpcId", "no-vpc")
            if vpc_id not in vpc_instances:
                vpc_instances[vpc_id] = []
            vpc_instances[vpc_id].append(instance)
        
        # Generate VPC clusters
        for vpc in data.get("vpcs", []):
            vpc_id = vpc["VpcId"]
            vpc_name = self._get_resource_name(vpc)
            
            code_lines.append(f'    with Cluster("VPC: {vpc_name}"):')
            
            # Add instances in this VPC
            instances_in_vpc = vpc_instances.get(vpc_id, [])
            for i, instance in enumerate(instances_in_vpc):
                instance_name = self._get_resource_name(instance)
                state = instance.get("State", {}).get("Name", "unknown")
                
                code_lines.append(
                    f'        instance_{i} = EC2("{instance_name}\\n{state}")'
                )
            
            # Add subnets in this VPC
            vpc_subnets = [s for s in data.get("subnets", []) if s.get("VpcId") == vpc_id]
            for subnet in vpc_subnets:
                subnet_name = self._get_resource_name(subnet)
                subnet_type = "Public" if self._is_public_subnet(subnet, data) else "Private"
                subnet_class = "PublicSubnet" if subnet_type == "Public" else "PrivateSubnet"
                
                code_lines.append(
                    f'        {subnet_class}("{subnet_name}")'
                )
        
        # Add instances not in any VPC (EC2-Classic)
        if "no-vpc" in vpc_instances:
            code_lines.append('    with Cluster("EC2-Classic"):')
            for i, instance in enumerate(vpc_instances["no-vpc"]):
                instance_name = self._get_resource_name(instance)
                state = instance.get("State", {}).get("Name", "unknown")
                
                code_lines.append(
                    f'        classic_instance_{i} = EC2("{instance_name}\\n{state}")'
                )
        
        return "\n".join(code_lines)
    
    def _get_resource_name(self, resource: Dict[str, Any]) -> str:
        """
        Get a human-readable name for a resource.
        
        Args:
            resource: AWS resource dictionary
            
        Returns:
            Resource name
        """
        # Try to get name from tags
        tags = resource.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "Unnamed")
        
        # Fallback to resource ID
        for id_key in ["InstanceId", "VpcId", "SubnetId", "GroupId"]:
            if id_key in resource:
                return resource[id_key]
        
        return "Unknown"
    
    def _is_public_subnet(self, subnet: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Determine if a subnet is public based on route tables.
        
        Args:
            subnet: Subnet dictionary
            data: Full EC2 data
            
        Returns:
            True if subnet is public, False otherwise
        """
        subnet_id = subnet.get("SubnetId")
        
        # Check route tables for internet gateway routes
        for rt in data.get("route_tables", []):
            # Check if this route table is associated with the subnet
            associations = rt.get("Associations", [])
            subnet_associated = any(
                assoc.get("SubnetId") == subnet_id for assoc in associations
            )
            
            if subnet_associated:
                # Check for internet gateway routes
                routes = rt.get("Routes", [])
                has_igw_route = any(
                    route.get("GatewayId", "").startswith("igw-") 
                    for route in routes
                )
                if has_igw_route:
                    return True
        
        return False
    
    def get_required_permissions(self) -> List[str]:
        """Get required AWS permissions for EC2 plugin."""
        return [
            "ec2:DescribeVpcs",
            "ec2:DescribeInstances",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSubnets",
            "ec2:DescribeInternetGateways",
            "ec2:DescribeRouteTables"
        ]