import unittest
from src.kustforge.core.diff import FileChange, DiffFormatter
import os

class TestDiffFormatter(unittest.TestCase):
    def setUp(self):
        self.change = FileChange(
            template_path='test.yaml.template',
            output_path='test.yaml',
            original_content='name: original\n',
            processed_content='name: processed\n'
        )

    def test_create_diff(self):
        # Execute
        diff = DiffFormatter.create_diff(
            self.change.template_path,
            self.change.output_path,
            self.change.original_content,
            self.change.processed_content
        )
        
        # Verify
        self.assertIn('Template: test.yaml.template', diff)
        self.assertIn('Generated: test.yaml', diff)
        self.assertIn('-name: original', diff)
        self.assertIn('+name: processed', diff)

    def test_show_changes(self):
        # This is a visual test, we just verify it doesn't raise exceptions
        DiffFormatter.show_changes([self.change])

    def test_get_relative_path(self):
        # Test with an absolute path
        # Create a test path using the current directory
        current_dir = os.getcwd()
        test_path = os.path.join(current_dir, 'test.yaml')
        
        # Test relative path conversion
        result = DiffFormatter._get_relative_path(test_path)
        
        # Verify the result is relative (doesn't start with /)
        self.assertFalse(result.startswith('/'))
        self.assertEqual('test.yaml', result) 