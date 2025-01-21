from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class ElastiCacheResource(AWSResource):
    """
    Resolver for ElastiCache cluster details. Supports retrieving endpoints,
    port numbers, and other cluster attributes.
    """
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve ElastiCache cluster attributes based on query parameters.
        
        Supported attributes:
        - endpoint: The cluster endpoint address
        - port: The cluster endpoint port
        - arn: The cluster ARN
        
        Args:
            query: Dictionary containing query parameters (cluster, attr)
            
        Returns:
            Resolved attribute value or None if not found
        """
        try:
            elasticache = self.get_client('elasticache')
            response = elasticache.describe_cache_clusters(
                CacheClusterId=query.get('cluster'),
                ShowCacheNodeInfo=True
            )
            
            if not response['CacheClusters']:
                return None
                
            cluster = response['CacheClusters'][0]
            attr = query.get('attr', 'endpoint')
            
            if attr == 'endpoint':
                return cluster['CacheNodes'][0]['Endpoint']['Address']
            elif attr == 'port':
                return str(cluster['CacheNodes'][0]['Endpoint']['Port'])
            elif attr == 'arn':
                return f"arn:aws:elasticache:{cluster['PreferredAvailabilityZone'][:-1]}:" \
                       f"{cluster['ARN']}"
                
            return None
            
        except ClientError as e:
            print(f"Error querying ElastiCache: {e}")
            return None