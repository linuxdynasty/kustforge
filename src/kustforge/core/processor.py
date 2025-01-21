import re
from typing import Dict, Any, List, Optional
from kustforge.core.diff import FileChange
from kustforge.utils.validation import TemplateValidator
from kustforge.aws.resolver import AWSResourceResolver

class TemplateProcessor:
    """Processes Kubernetes manifest templates"""
    
    def __init__(self, aws_resolver: Optional[AWSResourceResolver] = None):
        """
        Initialize the processor
        
        Args:
            aws_resolver: Optional AWS resource resolver for template processing.
                         If not provided, a default validator will be used.
        """
        self.validator = TemplateValidator()
        self.aws_resolver = aws_resolver

    def process_reference(self, reference: str) -> str:
        """
        Process a single reference and return the resolved value
        
        Args:
            reference: The reference string to process (e.g., 'aws:rds:name=test')
            
        Returns:
            Resolved value as a string
        """
        if not self.aws_resolver:
            raise ValueError("AWS resolver not configured")
            
        if not reference.startswith('aws:'):
            raise ValueError(f"Invalid reference format: {reference}")
            
        # Remove 'aws:' prefix
        aws_ref = reference[4:]
        return self.aws_resolver.resolve_aws_resource(aws_ref)

    def process_template(self, template: str, is_file: bool = True, validate: bool = True) -> str:
        """
        Process a template and return the processed content
        
        Args:
            template: Either a file path or template content string
            is_file: If True, template is a file path. If False, template is the content
            validate: If True, validates the processed content as a K8s manifest
            
        Returns:
            Processed template content as a string
        """
        # Get the content either from file or direct input
        if is_file:
            with open(template, 'r') as f:
                content = f.read()
        else:
            content = template
            
        # Process AWS references in the content
        def replace_reference(match):
            reference = match.group(1)
            try:
                return self.process_reference(reference)
            except ValueError as e:
                print(f"Warning: Failed to process reference {reference}: {str(e)}")
                return match.group(0)  # Return original if processing fails
                
        # Find all ${aws:...} references and replace them
        processed_content = re.sub(r'\${(aws:[^}]+)}', replace_reference, content)
        
        # Validate the processed content if requested
        if validate:
            errors = self.validator.validate_manifest(processed_content)
            if errors:
                raise ValueError(f"Template validation failed:\n" + "\n".join(errors))
            
        return processed_content

    def process_templates(self, template_paths: List[str]) -> List[FileChange]:
        """
        Process multiple templates and return FileChange objects
        
        Args:
            template_paths: List of template file paths
            
        Returns:
            List of FileChange objects containing the processed results
        """
        changes = []
        for template_path in template_paths:
            output_path = template_path.replace('.template', '')
            
            # Read original content if output file exists
            try:
                with open(output_path, 'r') as f:
                    original_content = f.read()
            except FileNotFoundError:
                original_content = ''
                
            # Process the template
            processed_content = self.process_template(template_path, is_file=True)
            
            # Create FileChange object
            change = FileChange(
                template_path=template_path,
                output_path=output_path,
                original_content=original_content,
                processed_content=processed_content
            )
            changes.append(change)
            
        return changes 