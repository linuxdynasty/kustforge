import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.session import AWSSessionManager

class TestAWSSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = AWSSessionManager(default_region='us-east-1')

    @patch('boto3.Session')
    def test_get_session_default(self, mock_session):
        # Test getting default session
        session = self.session_manager.get_session()
        mock_session.assert_called_once_with(region_name='us-east-1')
        self.assertEqual(session, mock_session.return_value)

    @patch('boto3.Session')
    def test_get_session_with_role(self, mock_session):
        # Setup
        mock_sts = Mock()
        mock_session.return_value.client.return_value = mock_sts
        mock_sts.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'test-key',
                'SecretAccessKey': 'test-secret',
                'SessionToken': 'test-token'
            }
        }
        
        # Execute
        session = self.session_manager.get_session(role_name='test-role', account_id='123456789012')
        
        # Verify
        mock_sts.assume_role.assert_called_once()
        mock_session.assert_called()

    def test_get_session_cached(self):
        # Setup
        mock_session = Mock()
        self.session_manager.sessions['default:default'] = mock_session
        
        # Execute
        session = self.session_manager.get_session()
        
        # Verify
        self.assertEqual(session, mock_session)

    def test_resolve_account_id(self):
        # Setup
        self.session_manager.account_mappings = {
            'prod': '123456789012',
            'dev': '210987654321'
        }
        
        # Test numeric account ID
        self.assertEqual(self.session_manager.resolve_account_id('123456789012'), '123456789012')
        
        # Test account alias
        self.assertEqual(self.session_manager.resolve_account_id('prod'), '123456789012')
        
        # Test unknown alias
        self.assertEqual(self.session_manager.resolve_account_id('unknown'), 'unknown') 