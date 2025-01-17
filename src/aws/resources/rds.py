from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class RDSResource(AWSResource):
    """Resolver for RDS instance details"""
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """Resolve RDS instance attributes"""
        try:
            rds = self.get_client('rds')
            response = rds.describe_db_instances(
                DBInstanceIdentifier=query.get('name')
            )
            
            if not response['DBInstances']:
                return None
                
            instance = response['DBInstances'][0]
            attr = query.get('attr', 'endpoint')
            
            if attr == 'endpoint':
                return instance['Endpoint']['Address']
            elif attr == 'port':
                return str(instance['Endpoint']['Port'])
            elif attr == 'arn':
                return instance['DBInstanceArn']
                
            return None
            
        except ClientError as e:
            print(f"Error querying RDS: {e}")
            return None
