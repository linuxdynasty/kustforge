import unittest
from unittest.mock import Mock, patch
import json
from src.kustforge.aws.resources.secrets import SecretsResource

class TestSecretsResource(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock()
        self.resource = SecretsResource(self.mock_session)

    def test_resolve_simple_secret(self):
        # Setup
        mock_secrets = Mock()
        self.mock_session.client.return_value = mock_secrets
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'mysecretvalue'
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'mysecret'
        })
        
        # Verify
        self.assertEqual(result, 'mysecretvalue')

    def test_resolve_json_secret_with_key(self):
        # Setup
        mock_secrets = Mock()
        self.mock_session.client.return_value = mock_secrets
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'username': 'admin',
                'password': 'secret123'
            })
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'mysecret',
            'key': 'username'
        })
        
        # Verify
        self.assertEqual(result, 'admin')

    def test_resolve_invalid_json_with_key(self):
        # Setup
        mock_secrets = Mock()
        self.mock_session.client.return_value = mock_secrets
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'not-json'
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'mysecret',
            'key': 'username'
        })
        
        # Verify
        self.assertIsNone(result) 