from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class WAFResource(AWSResource):
    """
    Resolver for AWS WAF (Web Application Firewall) details. Handles retrieving
    WAF ARNs and other attributes.
    """
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve WAF attributes based on query parameters.
        
        Supported attributes:
        - arn: The WAF ACL ARN
        
        Example usage:
            {{ aws:waf:name=mywaf,attr=arn }}
            {{ aws:role=staging:waf:name=mywaf,attr=arn }}
        
        Args:
            query: Dictionary containing query parameters (name, attr)
            
        Returns:
            Resolved attribute value or None if not found
        """
        try:
            wafv2 = self.get_client('wafv2')
            response = wafv2.list_web_acls(
                Scope='REGIONAL'  # or 'CLOUDFRONT' depending on your needs
            )
            
            name = query.get('name')
            attr = query.get('attr', 'arn')
            
            for waf in response['WebACLs']:
                if waf['Name'] == name:
                    if attr == 'arn':
                        return waf['ARN']
                    
            return None
            
        except ClientError as e:
            print(f"Error querying WAF: {e}")
            return None 