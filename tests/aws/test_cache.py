import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.cache import CachedResourceResolver

class TestCachedResourceResolver(unittest.TestCase):
    def setUp(self):
        self.mock_base_resolver = Mock()
        self.cache_resolver = CachedResourceResolver(self.mock_base_resolver)

    def test_parse_resource_identifier(self):
        # Setup
        expected_result = ('123456789012', 'role', 'rds', {'name': 'test'})
        self.mock_base_resolver.parse_resource_identifier.return_value = expected_result
        
        # Execute
        result = self.cache_resolver.parse_resource_identifier('aws:rds:name=test')
        
        # Verify
        self.assertEqual(result, expected_result)
        self.mock_base_resolver.parse_resource_identifier.assert_called_once_with('aws:rds:name=test')

    def test_resolve_aws_resource_cached(self):
        # Setup
        cache_key = 'account:role:rds:{"name": "test"}'
        expected_value = 'cached-value'
        
        # Pre-populate the cache with a known value
        self.mock_base_resolver.resolve_aws_resource.return_value = expected_value
        
        # First call to populate cache
        first_result = self.cache_resolver.resolve_aws_resource('rds', {'name': 'test'}, 'account', 'role')
        
        # Reset the mock to ensure subsequent calls don't use the base resolver
        self.mock_base_resolver.resolve_aws_resource.reset_mock()
        
        # Execute - second call should use cache
        second_result = self.cache_resolver.resolve_aws_resource('rds', {'name': 'test'}, 'account', 'role')
        
        # Verify
        self.assertEqual(second_result, expected_value)
        self.mock_base_resolver.resolve_aws_resource.assert_not_called()

    def test_resolve_aws_resource_uncached(self):
        # Setup
        self.mock_base_resolver.resolve_aws_resource.return_value = 'new-value'
        
        # Execute
        result = self.cache_resolver.resolve_aws_resource('rds', {'name': 'test'}, 'account', 'role')
        
        # Verify
        self.assertEqual(result, 'new-value')
        self.mock_base_resolver.resolve_aws_resource.assert_called_once_with(
            'rds', {'name': 'test'}, 'account', 'role'
        )

    def test_validate_resource_reference(self):
        # Setup
        self.mock_base_resolver.validate_resource_reference.return_value = True
        
        # Execute
        result = self.cache_resolver.validate_resource_reference('aws:rds:name=test')
        
        # Verify
        self.assertTrue(result)
        self.mock_base_resolver.validate_resource_reference.assert_called_once_with('aws:rds:name=test') 