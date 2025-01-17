import re
import yaml
import subprocess
from typing import Dict, Any, List, Optional
from core.diff import FileChange
from aws.resolver import AWSResourceResolver
from aws.session import AWSSessionManager

class TemplateValidator:
    """Validates processed Kubernetes manifests"""
    
    def __init__(self):
        # Create a minimal resolver just for validation
        session_manager = AWSSessionManager(default_region='us-east-1')  # Add default region
        self.aws_resolver = AWSResourceResolver(session_manager)

    def validate_manifest(self, content: str) -> List[str]:
        """
        Validate processed manifest content
        
        This method performs multiple validation checks:
        1. YAML structure
        2. Basic Kubernetes manifest structure
        """
        errors = []
        
        # Validate YAML structure
        try:
            yaml_content = yaml.safe_load(content)
            if not yaml_content:
                errors.append("Empty YAML document")
            elif not isinstance(yaml_content, dict):
                errors.append("Top-level YAML must be a mapping")
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {str(e)}")
        
        # Validate basic Kubernetes manifest structure
        if yaml_content and isinstance(yaml_content, dict):
            k8s_errors = self._validate_kubernetes_manifest(yaml_content)
            errors.extend(k8s_errors)
        
        return errors
    
    def _validate_aws_reference(self, ref: str) -> bool:
        """
        Validate AWS resource reference syntax
        """
        try:
            # Remove 'aws:' prefix if present
            if ref.startswith('aws:'):
                ref = ref[4:]
                
            print(f"Parsing reference: {ref}")  # Debug log
            
            # Use existing resolver's validation
            return self.aws_resolver.validate_resource_reference(ref)
            
        except Exception as e:
            print(f"Validation error: {str(e)}")  # Debug log
            return False
    
    def _validate_kubernetes_manifest(self, content: Dict[str, Any]) -> List[str]:
        """
        Validate basic Kubernetes manifest structure
        
        Checks for required fields and basic structural requirements
        of Kubernetes manifests.
        """
        errors = []
        
        required_fields = {'apiVersion', 'kind', 'metadata'}
        missing_fields = required_fields - set(content.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        if 'metadata' in content:
            if not isinstance(content['metadata'], dict):
                errors.append("metadata must be a mapping")
            elif 'name' not in content['metadata']:
                errors.append("metadata.name is required")
        
        return errors
    
    def validate_against_cluster(self, content: str) -> List[str]:
        """
        Validate processed manifest against target Kubernetes cluster
        
        This performs a server-side validation using kubectl dry-run
        to catch issues that would prevent successful application.
        """
        warnings = []
        
        try:
            # Use kubectl dry-run to validate against the cluster
            result = subprocess.run(
                ['kubectl', 'apply', '--dry-run=server', '-f', '-'],
                input=content.encode(),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                warnings.append(f"Cluster validation failed: {result.stderr}")
            elif result.stderr:
                # Capture warnings even if return code is 0
                warnings.append(f"Cluster validation warning: {result.stderr}")
                
        except Exception as e:
            warnings.append(f"Cluster validation error: {str(e)}")
        
        return warnings
    
    def validate_changes(self, changes: List[FileChange]) -> bool:
        """
        Validate all processed manifest changes before applying them
        
        Returns True if all validations pass, False otherwise.
        """
        all_valid = True
        
        for change in changes:
            # Skip non-Kubernetes manifest files
            if not change.output_path.endswith(('.yaml', '.yml')):
                continue
            
            # Validate processed content
            manifest_errors = self.validate_manifest(change.processed_content)
            manifest_warnings = self.validate_against_cluster(change.processed_content)
            
            if manifest_errors or manifest_warnings:
                all_valid = False
                print(f"\nValidation issues for {change.output_path}:")
                for error in manifest_errors:
                    print(f"  - Error: {error}")
                for warning in manifest_warnings:
                    print(f"  - Warning: {warning}")
        
        return all_valid