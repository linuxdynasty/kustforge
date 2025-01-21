import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.resolver import AWSResourceResolver

class TestAWSResourceResolver(unittest.TestCase):
    def setUp(self):
        self.mock_session_manager = Mock()
        self.resolver = AWSResourceResolver(self.mock_session_manager)

    def test_parse_resource_identifier_basic(self):
        # Test basic resource identifier
        account_id, role_name, resource_type, query = \
            self.resolver.parse_resource_identifier('aws:rds:name=test')
        
        self.assertIsNone(account_id)
        self.assertIsNone(role_name)
        self.assertEqual(resource_type, 'rds')
        self.assertEqual(query, {'name': 'test'})

    def test_parse_resource_identifier_with_role(self):
        # Test resource identifier with role
        account_id, role_name, resource_type, query = \
            self.resolver.parse_resource_identifier('aws:role=myrole:rds:name=test')
        
        self.assertIsNone(account_id)
        self.assertEqual(role_name, 'myrole')
        self.assertEqual(resource_type, 'rds')
        self.assertEqual(query, {'name': 'test'})

    def test_parse_resource_identifier_invalid(self):
        # Test invalid resource identifier
        with self.assertRaises(ValueError):
            self.resolver.parse_resource_identifier('invalid:format')

    def test_resolve_aws_resource(self):
        # Setup mock session and resource handler
        mock_session = Mock()
        self.mock_session_manager.get_session.return_value = mock_session
        
        mock_handler = Mock()
        mock_handler.resolve.return_value = 'resolved-value'
        
        with patch.dict(self.resolver.resource_handlers, {'rds': lambda x: mock_handler}):
            # Execute
            result = self.resolver.resolve_aws_resource('rds', {'name': 'test'})
            
            # Verify
            self.assertEqual(result, 'resolved-value')
            self.mock_session_manager.get_session.assert_called_once_with(None, None)
            mock_handler.resolve.assert_called_once_with({'name': 'test'})

    def test_get_supported_resource_types(self):
        # Execute
        result = self.resolver.get_supported_resource_types()
        
        # Verify
        self.assertIsInstance(result, list)
        self.assertIn('rds', result)
        self.assertIn('elasticache', result) 