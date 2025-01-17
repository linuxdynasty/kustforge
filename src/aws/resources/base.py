from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import boto3

class AWSResource(ABC):
    """Base class for AWS resource resolvers"""
    
    def __init__(self, session: boto3.Session):
        self.session = session
    
    @abstractmethod
    def resolve(self, query: Dict[str, str]) -> Optional[str]:
        """Resolve resource information based on query parameters"""
        pass
    
    def get_client(self, service: str) -> boto3.client:
        """Get AWS service client from session"""
        return self.session.client(service)
