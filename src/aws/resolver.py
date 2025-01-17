from typing import Dict, Optional, Tuple, Type
from botocore.exceptions import ClientError
import re
from .session import AWSSessionManager
from .resources.base import AWSResource
from .resources.rds import RDSResource
from .resources.elasticache import ElastiCacheResource
from .resources.alb import ALBResource
from .resources.ecr import ECRResource
from .resources.secrets import SecretsResource

class AWSResourceResolver:
    """
    Central coordinator for resolving AWS resource information across different services.
    
    This class manages the resolution of AWS resource references, handling authentication,
    resource type routing, and error handling. It supports cross-account access and
    role assumption for flexible resource resolution across an AWS organization.
    """
    
    def __init__(self, session_manager: AWSSessionManager):
        """
        Initialize the resolver with a session manager for AWS authentication.
        
        Args:
            session_manager: Manager for AWS session handling and credentials
        """
        self.session_manager = session_manager
        self.resource_handlers: Dict[str, Type[AWSResource]] = {
            'rds': RDSResource,
            'elasticache': ElastiCacheResource,
            'alb': ALBResource,
            'ecr': ECRResource,
            'secret': SecretsResource
        }
        
        # Updated pattern to handle aws:role=name format
        self.identifier_pattern = re.compile(
            r'^aws:'                     # Required aws prefix
            r'(?:role=([^:]+):)?'        # Optional role prefix
            r'([^:]+)'                   # Resource type
            r':(.+)$'                    # Query parameters
        )

    def parse_resource_identifier(self, identifier: str) -> Tuple[Optional[str], 
                                                                Optional[str], 
                                                                str, 
                                                                Dict[str, str]]:
        """
        Parse an AWS resource identifier into its components.
        
        The identifier format can be:
        - aws:role=myrole:elasticache:cluster=mycluster,attr=endpoint
        - aws:elasticache:cluster=mycluster
        
        Args:
            identifier: The resource identifier string
            
        Returns:
            Tuple of (account_id, role_name, resource_type, query_params)
        """
        # Don't modify the original identifier when matching
        match = self.identifier_pattern.match(identifier)
        if not match:
            print(f"Failed to match pattern for identifier: {identifier}")  # Debug line
            raise ValueError(f"Invalid resource identifier format: {identifier}")
        
        role_name, resource_type, query_str = match.groups()
        account_id = None  # We'll derive this from the role if needed
        
        # Parse query parameters with improved error handling
        query_params = {}
        if query_str:
            params = query_str.split(',')
            for param in params:
                param = param.strip()
                if not param:  # Skip empty parameters
                    continue
                if '=' not in param:
                    raise ValueError(f"Invalid parameter format (missing '='): {param}")
                
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if not key:
                    raise ValueError("Empty parameter key is not allowed")
                if not value:
                    raise ValueError(f"Empty value for parameter key '{key}' is not allowed")
                    
                query_params[key] = value
        
        return account_id, role_name, resource_type, query_params

    def resolve_aws_resource(self, resource_type: str, query: Dict[str, str],
                           account_id: Optional[str] = None, 
                           role_name: Optional[str] = None) -> Optional[str]:
        """
        Resolve an AWS resource reference to its actual value.
        
        This method:
        1. Gets the appropriate AWS session based on account/role
        2. Instantiates the correct resource handler
        3. Delegates the resolution to the handler
        4. Handles any errors that occur during resolution
        
        Args:
            resource_type: Type of AWS resource (e.g., 'rds', 'ecr')
            query: Dictionary of query parameters for the resource
            account_id: Optional AWS account ID for cross-account access
            role_name: Optional IAM role to assume
            
        Returns:
            Resolved resource value or None if resolution fails
            
        Raises:
            ValueError: If the resource type is unknown
        """
        # Validate resource type
        if resource_type not in self.resource_handlers:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        try:
            # Get AWS session with appropriate credentials
            session = self.session_manager.get_session(account_id, role_name)
            
            # Create and use the appropriate resource handler
            handler_class = self.resource_handlers[resource_type]
            handler = handler_class(session)
            
            return handler.resolve(query)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('AccessDenied', 'UnauthorizedOperation'):
                print(f"Access denied while resolving {resource_type} resource. "
                      f"Check IAM permissions for account {account_id or 'default'} "
                      f"and role {role_name or 'default'}")
            else:
                print(f"Error resolving {resource_type} resource: {str(e)}")
            return None
            
        except Exception as e:
            print(f"Unexpected error resolving {resource_type} resource: {str(e)}")
            return None

    def get_supported_resource_types(self) -> list[str]:
        """
        Get a list of supported AWS resource types.
        
        Returns:
            List of resource type identifiers that can be resolved
        """
        return list(self.resource_handlers.keys())

    def validate_resource_reference(self, identifier: str) -> bool:
        """
        Validate that a resource reference string is properly formatted.
        
        This method checks if the reference follows the correct syntax and
        refers to a supported resource type. It's useful for early validation
        before attempting resolution.
        
        Args:
            identifier: The resource reference string to validate
            
        Returns:
            True if the reference is valid, False otherwise
        """
        try:
            account_id, role_name, resource_type, query = \
                self.parse_resource_identifier(identifier)
                
            # Check if resource type is supported
            if resource_type not in self.resource_handlers:
                return False
            
            # Check if required query parameters are present
            handler_class = self.resource_handlers[resource_type]
            handler = handler_class(None)  # No session needed for validation
            required_params = getattr(handler, 'required_params', [])
            
            return all(param in query for param in required_params)
            
        except ValueError:
            return False