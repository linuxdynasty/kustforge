import sys
from pathlib import Path

# Add the src directory to Python path for tests
src_dir = str(Path(__file__).resolve().parents[1] / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from unittest.mock import patch, MagicMock
from kustforge.cli import main, parse_args

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.fixture_path = Path(__file__).parent / 'fixtures' / 'template.yaml'

    def test_parse_args_process(self):
        # Test process command
        args = parse_args(['process', str(self.fixture_path), '-o', 'output.yaml'])
        self.assertEqual(args.command, 'process')
        self.assertEqual(args.template, str(self.fixture_path))
        self.assertEqual(args.output, 'output.yaml')

    def test_parse_args_validate(self):
        # Test validate command
        args = parse_args(['validate', str(self.fixture_path)])
        self.assertEqual(args.command, 'validate')
        self.assertEqual(args.template, str(self.fixture_path))

    @patch('kustforge.cli.TemplateProcessor')
    @patch('kustforge.cli.TemplateValidator')
    def test_main_process(self, mock_validator, mock_processor):
        # Setup
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.process_template.return_value = 'processed content'
        
        # Execute
        with patch('sys.argv', ['cli.py', 'process', str(self.fixture_path)]):
            main()
        
        # Verify
        mock_processor_instance.process_template.assert_called_once()

    @patch('kustforge.cli.TemplateValidator')
    def test_main_validate(self, mock_validator):
        # Setup
        mock_validator_instance = MagicMock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_manifest.return_value = []
        
        # Execute
        with patch('sys.argv', ['cli.py', 'validate', str(self.fixture_path)]):
            main()
        
        # Verify
        mock_validator_instance.validate_manifest.assert_called_once()
