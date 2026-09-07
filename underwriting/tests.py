from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import Application


class ApplicationModelTestCase(TestCase):
    def setUp(self):
        self.underwriter = User.objects.create_user(
            username='underwriter1', password='testpass123'
        )

    def test_create_application_with_required_fields(self):
        app = Application.objects.create(
            applicant_name='John Doe',
            driver_age=35,
            vehicle_type='sedan',
            safety_rating=4,
            regional_risk_index=50,
            driving_experience_years=10,
        )
        self.assertEqual(app.applicant_name, 'John Doe')
        self.assertEqual(app.driver_age, 35)
        self.assertEqual(app.vehicle_type, 'sedan')
        self.assertEqual(app.safety_rating, 4)
        self.assertEqual(app.regional_risk_index, 50)
        self.assertEqual(app.driving_experience_years, 10)
        self.assertIsNotNone(app.created_at)
        self.assertIsNotNone(app.updated_at)

    def test_application_defaults_to_flagged_status(self):
        app = Application.objects.create(
            applicant_name='Jane Smith',
            driver_age=28,
            vehicle_type='suv',
            safety_rating=3,
            regional_risk_index=60,
            driving_experience_years=5,
        )
        self.assertEqual(app.status, 'flagged')

    def test_application_optional_fields_nullable(self):
        app = Application.objects.create(
            applicant_name='Bob Johnson',
            driver_age=45,
            vehicle_type='truck',
            safety_rating=5,
            regional_risk_index=40,
            driving_experience_years=20,
        )
        self.assertIsNone(app.calculated_risk_score)
        self.assertIsNone(app.initial_premium)
        self.assertIsNone(app.final_premium)
        self.assertIsNone(app.deductible_override)
        self.assertIsNone(app.risk_override_percentage)
        self.assertEqual(app.underwriter_notes, '')
        self.assertIsNone(app.underwriter_id)
        self.assertIsNone(app.decision_timestamp)

    def test_application_with_all_fields(self):
        now = timezone.now()
        app = Application.objects.create(
            applicant_name='Alice Brown',
            driver_age=30,
            vehicle_type='coupe',
            safety_rating=2,
            regional_risk_index=75,
            driving_experience_years=8,
            calculated_risk_score=65,
            initial_premium='1200.50',
            final_premium='1100.00',
            status='approved',
            deductible_override='500.00',
            risk_override_percentage='10.50',
            underwriter_notes='Good driving record',
            underwriter_id=self.underwriter,
            decision_timestamp=now,
        )
        self.assertEqual(app.applicant_name, 'Alice Brown')
        self.assertEqual(app.calculated_risk_score, 65)
        self.assertEqual(str(app.initial_premium), '1200.50')
        self.assertEqual(str(app.final_premium), '1100.00')
        self.assertEqual(app.status, 'approved')
        self.assertEqual(str(app.deductible_override), '500.00')
        self.assertEqual(str(app.risk_override_percentage), '10.50')
        self.assertEqual(app.underwriter_notes, 'Good driving record')
        self.assertEqual(app.underwriter_id, self.underwriter)

    def test_application_status_choices(self):
        for status, _ in Application.STATUS_CHOICES:
            app = Application.objects.create(
                applicant_name=f'Test {status}',
                driver_age=30,
                vehicle_type='sedan',
                safety_rating=3,
                regional_risk_index=50,
                driving_experience_years=5,
                status=status,
            )
            self.assertEqual(app.status, status)

    def test_application_vehicle_type_choices(self):
        for vehicle_type, _ in Application.VEHICLE_TYPE_CHOICES:
            app = Application.objects.create(
                applicant_name=f'Test {vehicle_type}',
                driver_age=30,
                vehicle_type=vehicle_type,
                safety_rating=3,
                regional_risk_index=50,
                driving_experience_years=5,
            )
            self.assertEqual(app.vehicle_type, vehicle_type)

    def test_application_ordering_by_created_at_descending(self):
        app1 = Application.objects.create(
            applicant_name='First',
            driver_age=30,
            vehicle_type='sedan',
            safety_rating=3,
            regional_risk_index=50,
            driving_experience_years=5,
        )
        app2 = Application.objects.create(
            applicant_name='Second',
            driver_age=35,
            vehicle_type='suv',
            safety_rating=4,
            regional_risk_index=60,
            driving_experience_years=10,
        )
        apps = list(Application.objects.all())
        self.assertEqual(apps[0].applicant_name, 'Second')
        self.assertEqual(apps[1].applicant_name, 'First')

    def test_application_str_representation(self):
        app = Application.objects.create(
            applicant_name='Test User',
            driver_age=30,
            vehicle_type='sedan',
            safety_rating=3,
            regional_risk_index=50,
            driving_experience_years=5,
            status='flagged',
        )
        self.assertEqual(str(app), 'Test User - Flagged')

    def test_application_verbose_name(self):
        self.assertEqual(Application._meta.verbose_name, 'Application')
