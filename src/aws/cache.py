from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from .resolver import AWSResourceResolver

class CachedResourceResolver:
    """Caches AWS resource resolution results to minimize API calls"""
    
    def __init__(self, base_resolver: AWSResourceResolver):
        self.base_resolver = base_resolver
        self.cache: Dict[str, str] = {}

    def parse_resource_identifier(self, identifier: str) -> Tuple[Optional[str], 
                                                                Optional[str], 
                                                                str, 
                                                                Dict[str, str]]:
        """
        Delegate parsing to the base resolver
        
        Args:
            identifier: The resource identifier string
            
        Returns:
            Tuple of (account_id, role_name, resource_type, query_params)
        """
        return self.base_resolver.parse_resource_identifier(identifier)

    def resolve_aws_resource(self, resource_type: str, query: Dict[str, str],
                           account_id: Optional[str] = None,
                           role_name: Optional[str] = None) -> Optional[str]:
        """
        Resolve AWS resource with caching
        """
        cache_key = f"{account_id}:{role_name}:{resource_type}:{str(query)}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        result = self.base_resolver.resolve_aws_resource(
            resource_type, query, account_id, role_name
        )
        
        if result is not None:
            self.cache[cache_key] = result
            
        return result

    def validate_resource_reference(self, identifier: str) -> bool:
        """
        Delegate validation to the base resolver
        """
        return self.base_resolver.validate_resource_reference(identifier)
