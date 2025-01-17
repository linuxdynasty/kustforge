import os
import sys
import argparse
from typing import Dict, Optional
from core.wrapper import KustomizeWrapper
from core.diff import DiffFormatter
from utils.validation import TemplateValidator

def parse_variables(vars_list: Optional[list] = None) -> Dict[str, str]:
    """
    Parse command line variables into a dictionary.
    
    The function handles variables passed in key=value format and ensures
    proper formatting of the resulting dictionary.
    
    Args:
        vars_list: List of strings in 'key=value' format
        
    Returns:
        Dictionary of parsed variables
    
    Example:
        Input: ["app_name=myapp", "replicas=3"]
        Output: {"app_name": "myapp", "replicas": "3"}
    """
    variables = {}
    if vars_list:
        for var in vars_list:
            try:
                key, value = var.split('=', 1)
                variables[key.strip()] = value.strip()
            except ValueError:
                print(f"Warning: Skipping invalid variable format: {var}")
    return variables

def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command line argument parser.
    
    This function centralizes all command line argument definitions and
    their help messages for better maintainability.
    
    Returns:
        Configured argument parser instance
    """
    parser = argparse.ArgumentParser(
        description='Kustomize wrapper with template processing and AWS resource resolution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Show changes without applying:
    %(prog)s -d ./k8s --aws-config ./aws-config.yaml --diff
    
  Apply changes and generate manifests:
    %(prog)s -d ./k8s --aws-config ./aws-config.yaml --apply
    
  Use with variables:
    %(prog)s -d ./k8s -v app_name=myapp -v replicas=3 --apply
        """
    )
    
    # Required arguments
    parser.add_argument('--directory', '-d', required=True,
                       help='Directory containing Kustomize files')
    
    # AWS configuration
    parser.add_argument('--aws-region',
                       help='AWS region for API calls (defaults to AWS_REGION env var)')
    parser.add_argument('--aws-config',
                       help='Path to AWS configuration YAML file')
    
    # Operation mode flags
    parser.add_argument('--diff', action='store_true',
                       help='Show changes without applying them')
    parser.add_argument('--apply', action='store_true',
                       help='Apply the changes and generate output files')
    
    # Additional options
    parser.add_argument('--vars', '-v', action='append',
                       help='Variables in key=value format (can be specified multiple times)')
    parser.add_argument('--kustomize-args',
                       help='Additional arguments to pass to kustomize',
                       default='')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable AWS resource caching')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip Kubernetes manifest validation')
    parser.add_argument('--cleanup-backups', action='store_true',
                       help='Clean up old backup files (older than 7 days)')
    
    return parser

def run_kustomize_build(directory: str, kustomize_args: str) -> bool:
    """
    Execute the kustomize build command with provided arguments.
    
    This function handles the actual execution of kustomize after our
    template processing is complete.
    
    Args:
        directory: The directory containing kustomization.yaml
        kustomize_args: Additional arguments to pass to kustomize
        
    Returns:
        True if kustomize build succeeds, False otherwise
    """
    print("\nRunning kustomize build...")
    kustomize_cmd = f"kustomize build {directory} {kustomize_args}"
    return_code = os.system(kustomize_cmd)
    
    if return_code != 0:
        print("\nError: kustomize build failed", file=sys.stderr)
        return False
    
    print("Kustomize build completed successfully")
    return True

def main() -> int:
    """
    Main entry point for the Kustomize wrapper script.
    """
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Parse template variables
        variables = parse_variables(args.vars)
        
        # Initialize the wrapper
        wrapper = KustomizeWrapper(
            aws_region=args.aws_region,
            aws_config=args.aws_config,
            use_caching=not args.no_cache
        )
        
        # Clean up old backups if requested
        if args.cleanup_backups:
            wrapper.rollback_manager.cleanup_old_backups(args.directory)
        
        # Process templates
        print(f"\nProcessing templates in {args.directory}...")
        changes = wrapper.process_files(args.directory, variables)
        
        if not changes:
            print("No changes detected.")
            return 0
        
        # Show diff if requested or if not applying
        if args.diff or not args.apply:
            DiffFormatter.show_changes(changes)
            
            if not args.apply:
                print("\nTo apply these changes, run with --apply")
                wrapper.remove_generated_files(changes)
                return 0
        
        # Apply changes if requested
        if args.apply:
            print("\nApplying changes...")
            
            # Apply the changes
            if not wrapper.apply_changes(changes):
                print("\nFailed to apply changes.", file=sys.stderr)
                return 1
            
            print("Changes applied successfully")
            
            # Run kustomize build
            if not run_kustomize_build(args.directory, args.kustomize_args):
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
