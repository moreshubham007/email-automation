from .test_base import BaseTestCase
from app.models import Template

class TestTemplates(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create test template
        self.template = Template(
            name='Test Template',
            description='Test Description',
            content='Hello {{name}}, Welcome to {{company}}!'
        )
        self.template.set_placeholders(['name', 'company'])
        db.session.add(self.template)
        db.session.commit()

    def test_create_template(self):
        template_data = {
            'name': 'New Template',
            'description': 'New Description',
            'content': 'Hi {{name}}, This is {{sender}}.'
        }
        
        response = self.client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify template was created
        template = Template.query.get(data['id'])
        self.assertIsNotNone(template)
        self.assertEqual(template.name, template_data['name'])
        self.assertEqual(set(template.get_placeholders()), {'name', 'sender'})

    def test_update_template(self):
        update_data = {
            'name': 'Updated Template',
            'content': 'Hello {{name}} from {{department}}!'
        }
        
        response = self.client.put(f'/api/templates/{self.template.id}',
                                 json=update_data,
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify template was updated
        template = Template.query.get(self.template.id)
        self.assertEqual(template.name, update_data['name'])
        self.assertEqual(set(template.get_placeholders()), {'name', 'department'})

    def test_delete_template(self):
        response = self.client.delete(f'/api/templates/{self.template.id}')
        
        self.assertEqual(response.status_code, 204)
        
        # Verify template was deleted
        template = Template.query.get(self.template.id)
        self.assertIsNone(template) 