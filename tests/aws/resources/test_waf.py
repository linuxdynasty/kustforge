import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.resources.waf import WAFResource

class TestWAFResource(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock()
        self.resource = WAFResource(self.mock_session)

    def test_resolve_waf_arn(self):
        # Setup
        mock_wafv2 = Mock()
        self.mock_session.client.return_value = mock_wafv2
        mock_wafv2.list_web_acls.return_value = {
            'WebACLs': [{
                'Name': 'mywaf',
                'ARN': 'arn:aws:wafv2:region:123456789012:regional/webacl/mywaf/123'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'mywaf',
            'attr': 'arn'
        })
        
        # Verify
        self.assertTrue(result.startswith('arn:aws:wafv2'))

    def test_resolve_waf_not_found(self):
        # Setup
        mock_wafv2 = Mock()
        self.mock_session.client.return_value = mock_wafv2
        mock_wafv2.list_web_acls.return_value = {
            'WebACLs': []
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'nonexistent',
            'attr': 'arn'
        })
        
        # Verify
        self.assertIsNone(result) 