import os
import yaml
import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError

class AWSSessionManager:
    """Manages AWS sessions and credentials across accounts"""
    
    def __init__(self, default_region: str, config_file: Optional[str] = None):
        self.default_region = default_region
        self.sessions = {}
        self.role_mappings = {}
        self.account_mappings = {}
        self.profile_mappings = {}
        
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
    
    def _load_config(self, config_file: str) -> None:
        """Load AWS configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                self.role_mappings = config.get('role_mappings', {})
                self.account_mappings = config.get('account_mappings', {})
                self.profile_mappings = config.get('profile_mappings', {})
        except Exception as e:
            print(f"Warning: Failed to load AWS config: {str(e)}")
    
    def resolve_account_id(self, account_identifier: str) -> str:
        """Convert account aliases to account IDs"""
        if account_identifier.isdigit():
            return account_identifier
        return self.account_mappings.get(account_identifier, account_identifier)
    
    def get_session(self, account_id: Optional[str] = None, 
                   role_name: Optional[str] = None) -> boto3.Session:
        """Get or create an AWS session for the specified account/role"""
        if account_id:
            account_id = self.resolve_account_id(account_id)
        
        session_key = f"{account_id or 'default'}:{role_name or 'default'}"
        
        if session_key not in self.sessions:
            self.sessions[session_key] = self._create_session(account_id, role_name)
        
        return self.sessions[session_key]
    
    def _create_session(self, account_id: Optional[str], 
                       role_name: Optional[str]) -> boto3.Session:
        """Create a new AWS session with appropriate credentials"""
        if not role_name:
            return boto3.Session(region_name=self.default_region)
            
        if role_name in self.profile_mappings:
            return boto3.Session(
                profile_name=self.profile_mappings[role_name],
                region_name=self.default_region
            )
        
        role_arn = self._get_role_arn(account_id, role_name)
        return self._assume_role_session(role_arn)
    
    def _get_role_arn(self, account_id: Optional[str], role_name: str) -> str:
        """Resolve role ARN from configuration or construct it"""
        if role_name.startswith('arn:aws:iam::'):
            return role_name
            
        role_arn = self.role_mappings.get(role_name)
        if not role_arn:
            if not account_id:
                raise ValueError(
                    f"Unknown role alias '{role_name}' and no account_id provided"
                )
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            
        return role_arn
    
    def _assume_role_session(self, role_arn: str) -> boto3.Session:
        """Create session by assuming the specified role"""
        sts = boto3.client('sts')
        try:
            response = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f'kustomize-wrapper-{os.getpid()}',
                DurationSeconds=3600
            )
            
            return boto3.Session(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken'],
                region_name=self.default_region
            )
        except ClientError as e:
            raise ValueError(f"Failed to assume role {role_arn}: {str(e)}")
