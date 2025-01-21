import sys
from pathlib import Path

# Add the src directory to Python path for tests
src_dir = str(Path(__file__).resolve().parents[2] / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from unittest.mock import Mock, patch, mock_open
from kustforge.core.processor import TemplateProcessor
from kustforge.aws.resolver import AWSResourceResolver
from kustforge.core.diff import FileChange

class TestTemplateProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_resolver = Mock(spec=AWSResourceResolver)
        self.processor = TemplateProcessor(aws_resolver=self.mock_resolver)

    def test_process_reference(self):
        # Setup
        self.mock_resolver.resolve_aws_resource.return_value = 'resolved-value'
        
        # Execute
        result = self.processor.process_reference('aws:rds:name=test')
        
        # Verify
        self.assertEqual(result, 'resolved-value')
        self.mock_resolver.resolve_aws_resource.assert_called_once_with('rds:name=test')

    def test_process_invalid_reference(self):
        # Test invalid reference format
        with self.assertRaises(ValueError):
            self.processor.process_reference('invalid:reference')

    def test_process_template(self):
        # Setup
        template_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: ${aws:ecr:name=test}
"""
        self.mock_resolver.resolve_aws_resource.return_value = 'test-image:latest'
        
        # Execute
        result = self.processor.process_template(template_content, is_file=False)
        
        # Verify
        self.assertIsNotNone(result)
        self.assertIn('test-image:latest', result)

    def test_process_template_from_file(self):
        # Test processing from file
        template_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
"""
        with patch('builtins.open', mock_open(read_data=template_content)):
            result = self.processor.process_template('test.yaml', is_file=True)
            self.assertIsNotNone(result)

    def test_process_templates(self):
        # Setup
        template_paths = ['test1.yaml.template', 'test2.yaml.template']
        template_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
"""
        # Mock file operations
        mock_files = {
            'test1.yaml.template': template_content,
            'test2.yaml.template': template_content,
            'test1.yaml': template_content,
            'test2.yaml': template_content
        }
        
        def mock_open_file(*args, **kwargs):
            file_mock = Mock()
            file_mock.read.return_value = mock_files[args[0]]
            return mock_open(read_data=file_mock.read()).return_value
            
        # Execute
        with patch('builtins.open', side_effect=mock_open_file):
            changes = self.processor.process_templates(template_paths)
        
        # Verify
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0].template_path, 'test1.yaml.template')
        self.assertEqual(changes[1].template_path, 'test2.yaml.template') 