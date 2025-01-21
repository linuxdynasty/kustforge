import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.resources.acm import ACMResource

class TestACMResource(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock()
        self.resource = ACMResource(self.mock_session)

    def test_resolve_certificate_arn(self):
        # Setup
        mock_acm = Mock()
        self.mock_session.client.return_value = mock_acm
        mock_acm.list_certificates.return_value = {
            'CertificateSummaryList': [{
                'DomainName': 'example.com',
                'CertificateArn': 'arn:aws:acm:region:123456789012:certificate/uuid'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'domain': 'example.com',
            'attr': 'arn'
        })
        
        # Verify
        self.assertEqual(result, 'arn:aws:acm:region:123456789012:certificate/uuid')
        mock_acm.list_certificates.assert_called_once()

    def test_resolve_certificate_not_found(self):
        # Setup
        mock_acm = Mock()
        self.mock_session.client.return_value = mock_acm
        mock_acm.list_certificates.return_value = {
            'CertificateSummaryList': []
        }
        
        # Execute
        result = self.resource.resolve({
            'domain': 'nonexistent.com',
            'attr': 'arn'
        })
        
        # Verify
        self.assertIsNone(result) 