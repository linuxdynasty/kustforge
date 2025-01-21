import unittest
from unittest.mock import Mock, patch
from src.kustforge.aws.resources.ecr import ECRResource

class TestECRResource(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock()
        self.resource = ECRResource(self.mock_session)

    def test_resolve_repository_url(self):
        # Setup
        mock_ecr = Mock()
        self.mock_session.client.return_value = mock_ecr
        mock_ecr.describe_repositories.return_value = {
            'repositories': [{
                'repositoryUri': '123456789012.dkr.ecr.region.amazonaws.com/myapp',
                'repositoryArn': 'arn:aws:ecr:region:123456789012:repository/myapp',
                'repositoryName': 'myapp'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'name': 'myapp',
            'attr': 'url'
        })
        
        # Verify
        self.assertEqual(result, '123456789012.dkr.ecr.region.amazonaws.com/myapp')

    def test_get_auth_token(self):
        # Setup
        mock_ecr = Mock()
        self.mock_session.client.return_value = mock_ecr
        mock_ecr.get_authorization_token.return_value = {
            'authorizationData': [{
                'authorizationToken': 'base64token'
            }]
        }
        
        # Execute
        result = self.resource.resolve({
            'attr': 'auth'
        })
        
        # Verify
        self.assertEqual(result, 'base64token')

    def test_get_image_tags(self):
        # Setup
        mock_ecr = Mock()
        self.mock_session.client.return_value = mock_ecr
        mock_ecr.list_images.return_value = {
            'imageIds': [
                {'imageTag': 'latest'},
                {'imageTag': 'v1.0.0'}
            ]
        }
        
        # Execute
        result = self.resource.get_image_tags('myapp')
        
        # Verify
        self.assertEqual(result, ['latest', 'v1.0.0'])

    def test_validate_repository_access(self):
        # Setup
        mock_ecr = Mock()
        self.mock_session.client.return_value = mock_ecr
        mock_ecr.describe_repositories.return_value = {
            'repositories': [{'repositoryName': 'myapp'}]
        }
        
        # Execute
        result = self.resource.validate_repository_access('myapp')
        
        # Verify
        self.assertTrue(result) 