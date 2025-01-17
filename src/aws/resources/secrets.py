import json
from typing import Dict, Optional
from botocore.exceptions import ClientError
from .base import AWSResource

class SecretsResource(AWSResource):
    """
    Resolver for AWS Secrets Manager secrets. Supports retrieving both
    entire secrets and specific keys within JSON secrets.
    """
    
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """
        Resolve secret values based on query parameters.
        
        The secret can be either a simple string or a JSON object. For JSON
        objects, you can specify a key to retrieve a specific value.
        
        Args:
            query: Dictionary containing query parameters (name, key)
            
        Returns:
            Resolved secret value or None if not found
        """
        try:
            secrets = self.get_client('secretsmanager')
            response = secrets.get_secret_value(
                SecretId=query.get('name')
            )
            
            if 'SecretString' not in response:
                return None
                
            secret_value = response['SecretString']
            key = query.get('key')
            
            # If key is specified, try to parse as JSON and get that key
            if key:
                try:
                    secret_data = json.loads(secret_value)
                    return str(secret_data.get(key))
                except json.JSONDecodeError:
                    print(f"Warning: Secret is not JSON but key '{key}' was requested")
                    return None
            
            return secret_value
            
        except ClientError as e:
            print(f"Error retrieving secret: {e}")
            return None