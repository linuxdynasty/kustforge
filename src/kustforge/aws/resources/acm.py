from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class ACMResource(AWSResource):
    """
    Resolver for AWS Certificate Manager (ACM) details. Handles retrieving
    certificate ARNs and other attributes.
    """
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve ACM certificate attributes based on query parameters.
        
        Supported attributes:
        - arn: The certificate ARN
        
        Example usage:
            {{ aws:acm:domain=example.com,attr=arn }}
            {{ aws:role=staging:acm:domain=example.com,attr=arn }}
        
        Args:
            query: Dictionary containing query parameters (domain, attr)
            
        Returns:
            Resolved attribute value or None if not found
        """
        try:
            acm = self.get_client('acm')
            response = acm.list_certificates()
            
            domain = query.get('domain')
            attr = query.get('attr', 'arn')
            
            for cert in response['CertificateSummaryList']:
                if cert['DomainName'] == domain:
                    if attr == 'arn':
                        return cert['CertificateArn']
                    
            return None
            
        except ClientError as e:
            print(f"Error querying ACM: {e}")
            return None
