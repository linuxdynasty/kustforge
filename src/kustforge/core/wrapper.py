import re
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directory to Python path for direct script execution
parent_dir = str(Path(__file__).resolve().parents[2])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Use relative imports when running directly
if __package__ is None:
    from kustforge.aws.session import AWSSessionManager
    from kustforge.aws.resolver import AWSResourceResolver
    from kustforge.aws.cache import CachedResourceResolver
    from kustforge.utils.validation import TemplateValidator
    from kustforge.utils.rollback import RollbackManager
    from kustforge.core.diff import FileChange
else:
    # Use absolute imports when installed as a package
    from kustforge.aws.session import AWSSessionManager
    from kustforge.aws.resolver import AWSResourceResolver
    from kustforge.aws.cache import CachedResourceResolver
    from kustforge.utils.validation import TemplateValidator
    from kustforge.utils.rollback import RollbackManager
    from kustforge.core.diff import FileChange

class KustomizeWrapper:
    """Main class for processing Kustomize templates with AWS integration"""
    
    def __init__(self, aws_region: str = None, aws_config: str = None,
                 use_caching: bool = True):
        self.aws_region = aws_region or os.environ.get('AWS_REGION', 'us-east-1')
        self.session_manager = AWSSessionManager(self.aws_region, aws_config)
        
        # Initialize resource resolver with optional caching
        base_resolver = AWSResourceResolver(self.session_manager)
        self.aws_resolver = (CachedResourceResolver(base_resolver) 
                           if use_caching else base_resolver)
                           
        self.validator = TemplateValidator()
        self.rollback_manager = RollbackManager()
        self.variable_pattern = re.compile(r'{{\s*(.+?)\s*}}')

    def process_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Process template variables, including AWS resource references"""
        def replace_variable(match):
            var_name = match.group(1)
            
            if var_name.startswith('aws:'):
                account_id, role_name, resource_type, query = \
                    self.aws_resolver.parse_resource_identifier(var_name)
                return self.aws_resolver.resolve_aws_resource(
                    resource_type, query, account_id=account_id, role_name=role_name
                ) or match.group(0)
            
            return str(variables.get(var_name, match.group(0)))
        
        return self.variable_pattern.sub(replace_variable, content)

    def process_files(self, directory: str, variables: Dict[str, Any]) -> List[FileChange]:
        """Process template files and generate Kubernetes manifests"""
        changes = []
        
        # Backup existing manifests before making changes
        self.rollback_manager.backup_existing_manifests(directory)
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith('.') and file.endswith(('.yaml.template', '.yml.template')):
                    template_path = os.path.join(root, file)
                    output_path = os.path.join(
                        root,
                        file.replace('.template', '').lstrip('.')
                    )
                    
                    with open(template_path, 'r') as f:
                        original_content = f.read()
                    
                    processed_content = self.process_variables(
                        original_content,
                        variables
                    )
                    
                    changes.append(FileChange(
                        template_path=template_path,
                        output_path=output_path,
                        original_content=original_content,
                        processed_content=processed_content
                    ))
        
        return changes

    def apply_changes(self, changes: List[FileChange], dry_run: bool = False) -> bool:
        """Apply changes with validation and optional rollback"""
        try:
            if dry_run:
                return self.validator.validate_changes(changes)
            
            for change in changes:
                with open(change.output_path, 'w') as f:
                    f.write(change.processed_content)
            return True
            
        except Exception as e:
            print(f"Error applying changes: {str(e)}")
            self.rollback_manager.restore_manifests()
            return False

    def remove_generated_files(self, changes: List[FileChange]):
        """Remove the generated files from the processed changes.
        
        Args:
            changes (List[FileChange]): List of file changes from process_files()
        """
        import os
        
        for change in changes:
            if os.path.exists(change.output_path):
                os.remove(change.output_path)
