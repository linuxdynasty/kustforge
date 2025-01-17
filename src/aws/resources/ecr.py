from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class ECRResource(AWSResource):
    """
    Resolver for Amazon Elastic Container Registry (ECR) repository information.
    
    This class handles the resolution of ECR repository attributes such as repository
    URLs, ARNs, and names. It's particularly useful when working with container-based
    applications where you need to reference ECR repositories in Kubernetes manifests.
    
    The resolver supports retrieving:
    - Repository URIs for image references
    - Repository ARNs for IAM policies
    - Repository names for registry operations
    - Authentication tokens for Docker login
    """
    
    def __init__(self, session):
        """
        Initialize the ECR resource handler with an AWS session.
        
        Args:
            session: Boto3 session with appropriate ECR permissions
        """
        super().__init__(session)
        # Define required parameters for validation
        self.required_params = ['name']
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve ECR repository attributes based on query parameters.
        
        Supported attributes:
        - url: The repository URI (default)
        - arn: The repository ARN
        - name: The repository name
        - auth: Base64-encoded authentication token
        
        Example queries:
        - {{ aws:123456789012:ecr:name=myapp,attr=url }}
        - {{ aws:123456789012:ecr:name=myapp,attr=arn }}
        
        Args:
            query: Dictionary containing query parameters including:
                  - name: Repository name (required)
                  - attr: Attribute to resolve (optional, defaults to 'url')
            
        Returns:
            Resolved attribute value or None if resolution fails
        """
        try:
            # Get the ECR client from the session
            ecr = self.get_client('ecr')
            
            # Handle auth token requests separately as they don't need repository details
            if query.get('attr') == 'auth':
                return self._get_auth_token(ecr)
            
            # For all other attributes, we need repository details
            response = ecr.describe_repositories(
                repositoryNames=[query.get('name')]
            )
            
            if not response['repositories']:
                print(f"ECR repository not found: {query.get('name')}")
                return None
            
            # Get the repository details
            repo = response['repositories'][0]
            attr = query.get('attr', 'url')
            
            # Resolve the requested attribute
            if attr == 'url':
                return repo['repositoryUri']
            elif attr == 'arn':
                return repo['repositoryArn']
            elif attr == 'name':
                return repo['repositoryName']
            else:
                print(f"Unsupported ECR attribute: {attr}")
                return None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'RepositoryNotFoundException':
                print(f"ECR repository not found: {query.get('name')}")
            elif error_code in ('AccessDeniedException', 'UnauthorizedOperation'):
                print(f"Access denied to ECR repository. Check IAM permissions.")
            else:
                print(f"Error querying ECR: {e}")
            return None
    
    def _get_auth_token(self, ecr_client) -> Optional[str]:
        """
        Get an ECR authentication token for Docker login.
        
        This helper method retrieves a base64-encoded auth token that can be used
        with the Docker login command to authenticate with ECR.
        
        Args:
            ecr_client: Boto3 ECR client to use for the API call
            
        Returns:
            Base64-encoded auth token or None if retrieval fails
        """
        try:
            response = ecr_client.get_authorization_token()
            if response['authorizationData']:
                return response['authorizationData'][0]['authorizationToken']
            return None
        except ClientError as e:
            print(f"Error getting ECR auth token: {e}")
            return None
    
    def validate_repository_access(self, repository_name: str) -> bool:
        """
        Validate access to an ECR repository before attempting operations.
        
        This method checks if the current credentials have permission to access
        the specified repository. It's useful for early validation before
        attempting to use the repository in deployments.
        
        Args:
            repository_name: Name of the ECR repository to validate
            
        Returns:
            True if repository is accessible, False otherwise
        """
        try:
            ecr = self.get_client('ecr')
            ecr.describe_repositories(repositoryNames=[repository_name])
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'RepositoryNotFoundException':
                print(f"Repository does not exist: {repository_name}")
            elif error_code in ('AccessDeniedException', 'UnauthorizedOperation'):
                print(f"No access to repository: {repository_name}")
            else:
                print(f"Error validating repository access: {e}")
            return False
    
    def get_image_tags(self, repository_name: str, 
                      max_results: int = 100) -> Optional[list[str]]:
        """
        Get available image tags for a repository.
        
        This helper method retrieves the list of available image tags in a repository.
        It's useful for validation and for providing feedback about available versions.
        
        Args:
            repository_name: Name of the ECR repository
            max_results: Maximum number of tags to retrieve
            
        Returns:
            List of image tags or None if retrieval fails
        """
        try:
            ecr = self.get_client('ecr')
            response = ecr.list_images(
                repositoryName=repository_name,
                maxResults=max_results,
                filter={'tagStatus': 'TAGGED'}
            )
            
            if not response['imageIds']:
                return []
            
            return sorted(
                list({image['imageTag'] for image in response['imageIds'] 
                      if 'imageTag' in image})
            )
            
        except ClientError as e:
            print(f"Error retrieving image tags: {e}")
            return None