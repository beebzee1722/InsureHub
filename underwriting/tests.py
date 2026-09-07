from django.test import TestCase
from .models import Application


class ApplicationTestCase(TestCase):
    def test_application_creation(self):
        app = Application.objects.create(name="Test Application")
        self.assertEqual(app.name, "Test Application")
        self.assertIsNotNone(app.created_at)
