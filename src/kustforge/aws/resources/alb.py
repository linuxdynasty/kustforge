from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class ALBResource(AWSResource):
    """
    Resolver for Application Load Balancer details. Handles retrieving
    DNS names, ARNs, and hosted zone IDs.
    """
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve ALB attributes based on query parameters.
        
        Supported attributes:
        - dns: The ALB's DNS name
        - arn: The ALB's ARN
        - zone_id: The ALB's hosted zone ID
        
        Args:
            query: Dictionary containing query parameters (name, attr)
            
        Returns:
            Resolved attribute value or None if not found
        """
        try:
            elbv2 = self.get_client('elbv2')
            response = elbv2.describe_load_balancers(
                Names=[query.get('name')]
            )
            
            if not response['LoadBalancers']:
                return None
                
            lb = response['LoadBalancers'][0]
            attr = query.get('attr', 'dns')
            
            if attr == 'dns':
                return lb['DNSName']
            elif attr == 'arn':
                return lb['LoadBalancerArn']
            elif attr == 'zone_id':
                return lb['CanonicalHostedZoneId']
                
            return None
            
        except ClientError as e:
            print(f"Error querying ALB: {e}")
            return None