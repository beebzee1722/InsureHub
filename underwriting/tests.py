from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import Application
from .forms import ApplicationForm


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


class ApplicationFormTestCase(TestCase):
    def test_valid_form_submission(self):
        data = {
            'applicant_name': 'John Doe',
            'driver_age': 35,
            'vehicle_type': 'sedan',
            'safety_rating': 4,
            'regional_risk_index': 50,
            'driving_experience_years': 10,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())

    def test_driver_age_too_young(self):
        data = {
            'applicant_name': 'Jane Smith',
            'driver_age': 17,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 50,
            'driving_experience_years': 0,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('driver_age', form.errors)

    def test_driver_age_too_old(self):
        data = {
            'applicant_name': 'Jane Smith',
            'driver_age': 101,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 50,
            'driving_experience_years': 50,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('driver_age', form.errors)

    def test_safety_rating_too_low(self):
        data = {
            'applicant_name': 'Bob Johnson',
            'driver_age': 30,
            'vehicle_type': 'sedan',
            'safety_rating': 0,
            'regional_risk_index': 50,
            'driving_experience_years': 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('safety_rating', form.errors)

    def test_safety_rating_too_high(self):
        data = {
            'applicant_name': 'Bob Johnson',
            'driver_age': 30,
            'vehicle_type': 'sedan',
            'safety_rating': 6,
            'regional_risk_index': 50,
            'driving_experience_years': 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('safety_rating', form.errors)

    def test_regional_risk_index_too_low(self):
        data = {
            'applicant_name': 'Alice Brown',
            'driver_age': 30,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 0,
            'driving_experience_years': 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('regional_risk_index', form.errors)

    def test_regional_risk_index_too_high(self):
        data = {
            'applicant_name': 'Alice Brown',
            'driver_age': 30,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 101,
            'driving_experience_years': 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('regional_risk_index', form.errors)

    def test_driving_experience_exceeds_age(self):
        data = {
            'applicant_name': 'Young Driver',
            'driver_age': 25,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 50,
            'driving_experience_years': 10,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_driving_experience_at_max_allowed(self):
        data = {
            'applicant_name': 'Experienced Driver',
            'driver_age': 35,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 50,
            'driving_experience_years': 17,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())

    def test_form_excludes_calculated_fields(self):
        data = {
            'applicant_name': 'Test User',
            'driver_age': 30,
            'vehicle_type': 'sedan',
            'safety_rating': 3,
            'regional_risk_index': 50,
            'driving_experience_years': 8,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())
        self.assertNotIn('calculated_risk_score', form.fields)
        self.assertNotIn('initial_premium', form.fields)
        self.assertNotIn('final_premium', form.fields)
        self.assertNotIn('status', form.fields)
        self.assertNotIn('underwriter_notes', form.fields)
