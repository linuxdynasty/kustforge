import argparse
from kustforge.utils.validation import TemplateValidator
from kustforge.core.processor import TemplateProcessor

def parse_args(args=None):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Kubernetes Template Processor')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Process command
    process_parser = subparsers.add_parser('process', help='Process a template')
    process_parser.add_argument('template', help='Template file to process')
    process_parser.add_argument('-o', '--output', help='Output file', default=None)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a template')
    validate_parser.add_argument('template', help='Template file to validate')

    return parser.parse_args(args)

def main():
    """Main entry point for the CLI"""
    args = parse_args()

    if args.command == 'process':
        processor = TemplateProcessor()
        processed = processor.process_template(args.template)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(processed)
        else:
            print(processed)

    elif args.command == 'validate':
        validator = TemplateValidator()
        with open(args.template) as f:
            content = f.read()
        errors = validator.validate_manifest(content)
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            exit(1)
        print("Validation successful")

if __name__ == '__main__':
    main() 