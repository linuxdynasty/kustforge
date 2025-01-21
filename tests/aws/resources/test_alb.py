import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.resources.alb import ALBResource

class TestALBResource(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock()
        self.resource = ALBResource(self.mock_session)

    def test_resolve_alb_dns(self):
        # Setup
        mock_elbv2 = Mock()
        self.mock_session.client.return_value = mock_elbv2
        mock_elbv2.describe_load_balancers.return_value = {
            'LoadBalancers': [{
                'DNSName': 'my-alb-123.region.elb.amazonaws.com',
                'LoadBalancerArn': 'arn:aws:elasticloadbalancing:region:123456789012:loadbalancer/app/my-alb/123',
                'CanonicalHostedZoneId': 'Z123456789'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'my-alb',
            'attr': 'dns'
        })
        
        # Verify
        self.assertEqual(result, 'my-alb-123.region.elb.amazonaws.com')

    def test_resolve_alb_arn(self):
        # Setup
        mock_elbv2 = Mock()
        self.mock_session.client.return_value = mock_elbv2
        mock_elbv2.describe_load_balancers.return_value = {
            'LoadBalancers': [{
                'LoadBalancerArn': 'arn:aws:elasticloadbalancing:region:123456789012:loadbalancer/app/my-alb/123'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'my-alb',
            'attr': 'arn'
        })
        
        # Verify
        self.assertTrue(result.startswith('arn:aws:elasticloadbalancing'))

    def test_resolve_alb_not_found(self):
        # Setup
        mock_elbv2 = Mock()
        self.mock_session.client.return_value = mock_elbv2
        mock_elbv2.describe_load_balancers.return_value = {
            'LoadBalancers': []
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'nonexistent-alb'
        })
        
        # Verify
        self.assertIsNone(result) 