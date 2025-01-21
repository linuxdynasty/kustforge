import sys
from pathlib import Path

# Add the src directory to Python path for tests
src_dir = str(Path(__file__).resolve().parents[2] / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from unittest.mock import Mock, patch
from kustforge.utils.validation import TemplateValidator
from kustforge.core.diff import FileChange

class TestTemplateValidator(unittest.TestCase):
    def setUp(self):
        self.validator = TemplateValidator()

    def test_validate_manifest_valid(self):
        # Test valid manifest
        content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx
"""
        errors = self.validator.validate_manifest(content)
        self.assertEqual(len(errors), 0)

    def test_validate_manifest_invalid_yaml(self):
        # Test invalid YAML
        content = "invalid: yaml: structure:"
        errors = self.validator.validate_manifest(content)
        self.assertTrue(any('Invalid YAML syntax' in error for error in errors))

    def test_validate_manifest_missing_fields(self):
        # Test missing required fields
        content = """
kind: Pod
metadata:
  name: test-pod
"""
        errors = self.validator.validate_manifest(content)
        self.assertTrue(any('Missing required fields' in error for error in errors))

    @patch('subprocess.run')
    def test_validate_against_cluster(self, mock_run):
        # Setup mock subprocess
        mock_run.return_value = Mock(returncode=0, stderr='')
        
        # Test cluster validation
        warnings = self.validator.validate_against_cluster('valid: manifest')
        self.assertEqual(len(warnings), 0)
        mock_run.assert_called_once()

    def test_validate_changes(self):
        # Setup test changes
        changes = [
            FileChange(
                template_path='test.yaml.template',
                output_path='test.yaml',
                original_content='',
                processed_content="""
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
"""
            )
        ]
        
        # Test validation
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr='')
            result = self.validator.validate_changes(changes)
            self.assertTrue(result) 