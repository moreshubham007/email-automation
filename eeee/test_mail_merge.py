from unittest.mock import patch, MagicMock
import json
import io
from .test_base import BaseTestCase
from app.models import Template, Project, GmailAccount

class TestMailMerge(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create test data
        self.project = Project(
            name='Test Project',
            client_secret_path=os.path.join(self.temp_dir, 'client_secret.json')
        )
        db.session.add(self.project)
        
        self.gmail_account = GmailAccount(
            email='sender@gmail.com',
            project=self.project,
            authenticated=True,
            credentials=json.dumps({
                'token': 'test-token',
                'refresh_token': 'test-refresh-token',
                'token_uri': 'test-uri',
                'client_id': 'test-id',
                'client_secret': 'test-secret',
                'scopes': ['test-scope']
            })
        )
        db.session.add(self.gmail_account)
        
        self.template = Template(
            name='Test Template',
            content='Hello {{name}} from {{company}}!'
        )
        self.template.set_placeholders(['name', 'company'])
        db.session.add(self.template)
        db.session.commit()
        
        # Save mock client secret
        with open(self.project.client_secret_path, 'w') as f:
            json.dump(self.client_secret_content, f)

    def test_validate_csv(self):
        csv_content = 'recipient_email,sender_email,name,company\n'
        csv_content += 'recipient@test.com,sender@gmail.com,John,ACME Inc\n'
        csv_content += 'invalid-email,sender@gmail.com,Jane,XYZ Corp'
        
        csv_file = (io.BytesIO(csv_content.encode()), 'test.csv')
        
        response = self.client.post('/api/mail-merge/validate',
                                  data={
                                      'csv_file': csv_file,
                                      'template_id': self.template.id
                                  },
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify validation results
        self.assertEqual(len(data['valid_entries']), 1)
        self.assertEqual(len(data['invalid_entries']), 1)
        self.assertEqual(data['valid_entries'][0]['recipient_email'], 'recipient@test.com')

    @patch('app.utils.oauth_utils.build')
    def test_create_draft(self, mock_build):
        # Mock Gmail API service
        mock_service = MagicMock()
        mock_draft = {'id': 'test-draft-id'}
        mock_service.users().drafts().create().execute.return_value = mock_draft
        mock_build.return_value = mock_service
        
        merge_data = {
            'entry': {
                'recipient_email': 'recipient@test.com',
                'sender_email': 'sender@gmail.com',
                'name': 'John',
                'company': 'ACME Inc'
            },
            'template_id': self.template.id,
            'test_mode': False
        }
        
        response = self.client.post('/api/mail-merge/process',
                                  json=merge_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify draft was created
        self.assertTrue(data['success'])
        self.assertEqual(data['draft_id'], 'test-draft-id')
        
        # Verify API calls
        mock_service.users().drafts().create.assert_called_once() 