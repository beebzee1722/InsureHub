from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .forms import ApplicationForm
from .models import Application
from .services import calculate_premium, calculate_premium_with_overrides


class ApplicationModelTestCase(TestCase):
    def setUp(self):
        self.underwriter = User.objects.create_user(
            username="underwriter1", password="testpass123"
        )

    def test_create_application_with_required_fields(self):
        app = Application.objects.create(
            applicant_name="John Doe",
            driver_age=35,
            vehicle_type="sedan",
            safety_rating=4,
            regional_risk_index=50,
            driving_experience_years=10,
        )
        self.assertEqual(app.applicant_name, "John Doe")
        self.assertEqual(app.driver_age, 35)
        self.assertEqual(app.vehicle_type, "sedan")
        self.assertEqual(app.safety_rating, 4)
        self.assertEqual(app.regional_risk_index, 50)
        self.assertEqual(app.driving_experience_years, 10)
        self.assertIsNotNone(app.created_at)
        self.assertIsNotNone(app.updated_at)

    def test_application_defaults_to_flagged_status(self):
        app = Application.objects.create(
            applicant_name="Jane Smith",
            driver_age=28,
            vehicle_type="suv",
            safety_rating=3,
            regional_risk_index=60,
            driving_experience_years=5,
        )
        self.assertEqual(app.status, "flagged")

    def test_application_optional_fields_nullable(self):
        app = Application.objects.create(
            applicant_name="Bob Johnson",
            driver_age=45,
            vehicle_type="truck",
            safety_rating=5,
            regional_risk_index=40,
            driving_experience_years=20,
        )
        self.assertIsNone(app.calculated_risk_score)
        self.assertIsNone(app.initial_premium)
        self.assertIsNone(app.final_premium)
        self.assertIsNone(app.deductible_override)
        self.assertIsNone(app.risk_override_percentage)
        self.assertEqual(app.underwriter_notes, "")
        self.assertIsNone(app.underwriter_id)
        self.assertIsNone(app.decision_timestamp)

    def test_application_with_all_fields(self):
        now = timezone.now()
        app = Application.objects.create(
            applicant_name="Alice Brown",
            driver_age=30,
            vehicle_type="coupe",
            safety_rating=2,
            regional_risk_index=75,
            driving_experience_years=8,
            calculated_risk_score=65,
            initial_premium="1200.50",
            final_premium="1100.00",
            status="approved",
            deductible_override="500.00",
            risk_override_percentage="10.50",
            underwriter_notes="Good driving record",
            underwriter_id=self.underwriter,
            decision_timestamp=now,
        )
        self.assertEqual(app.applicant_name, "Alice Brown")
        self.assertEqual(app.calculated_risk_score, 65)
        self.assertEqual(str(app.initial_premium), "1200.50")
        self.assertEqual(str(app.final_premium), "1100.00")
        self.assertEqual(app.status, "approved")
        self.assertEqual(str(app.deductible_override), "500.00")
        self.assertEqual(str(app.risk_override_percentage), "10.50")
        self.assertEqual(app.underwriter_notes, "Good driving record")
        self.assertEqual(app.underwriter_id, self.underwriter)

    def test_application_status_choices(self):
        for status, _ in Application.STATUS_CHOICES:
            app = Application.objects.create(
                applicant_name=f"Test {status}",
                driver_age=30,
                vehicle_type="sedan",
                safety_rating=3,
                regional_risk_index=50,
                driving_experience_years=5,
                status=status,
            )
            self.assertEqual(app.status, status)

    def test_application_vehicle_type_choices(self):
        for vehicle_type, _ in Application.VEHICLE_TYPE_CHOICES:
            app = Application.objects.create(
                applicant_name=f"Test {vehicle_type}",
                driver_age=30,
                vehicle_type=vehicle_type,
                safety_rating=3,
                regional_risk_index=50,
                driving_experience_years=5,
            )
            self.assertEqual(app.vehicle_type, vehicle_type)

    def test_application_ordering_by_created_at_descending(self):
        Application.objects.create(
            applicant_name="First",
            driver_age=30,
            vehicle_type="sedan",
            safety_rating=3,
            regional_risk_index=50,
            driving_experience_years=5,
        )
        Application.objects.create(
            applicant_name="Second",
            driver_age=35,
            vehicle_type="suv",
            safety_rating=4,
            regional_risk_index=60,
            driving_experience_years=10,
        )
        apps = list(Application.objects.all())
        self.assertEqual(apps[0].applicant_name, "Second")
        self.assertEqual(apps[1].applicant_name, "First")

    def test_application_str_representation(self):
        app = Application.objects.create(
            applicant_name="Test User",
            driver_age=30,
            vehicle_type="sedan",
            safety_rating=3,
            regional_risk_index=50,
            driving_experience_years=5,
            status="flagged",
        )
        self.assertEqual(str(app), "Test User - Flagged")

    def test_application_verbose_name(self):
        self.assertEqual(Application._meta.verbose_name, "Application")


class ApplicationFormTestCase(TestCase):
    def test_valid_form_submission(self):
        data = {
            "applicant_name": "John Doe",
            "driver_age": 35,
            "vehicle_type": "sedan",
            "safety_rating": 4,
            "regional_risk_index": 50,
            "driving_experience_years": 10,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())

    def test_driver_age_too_young(self):
        data = {
            "applicant_name": "Jane Smith",
            "driver_age": 17,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 50,
            "driving_experience_years": 0,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("driver_age", form.errors)

    def test_driver_age_too_old(self):
        data = {
            "applicant_name": "Jane Smith",
            "driver_age": 101,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 50,
            "driving_experience_years": 50,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("driver_age", form.errors)

    def test_safety_rating_too_low(self):
        data = {
            "applicant_name": "Bob Johnson",
            "driver_age": 30,
            "vehicle_type": "sedan",
            "safety_rating": 0,
            "regional_risk_index": 50,
            "driving_experience_years": 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("safety_rating", form.errors)

    def test_safety_rating_too_high(self):
        data = {
            "applicant_name": "Bob Johnson",
            "driver_age": 30,
            "vehicle_type": "sedan",
            "safety_rating": 6,
            "regional_risk_index": 50,
            "driving_experience_years": 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("safety_rating", form.errors)

    def test_regional_risk_index_too_low(self):
        data = {
            "applicant_name": "Alice Brown",
            "driver_age": 30,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 0,
            "driving_experience_years": 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("regional_risk_index", form.errors)

    def test_regional_risk_index_too_high(self):
        data = {
            "applicant_name": "Alice Brown",
            "driver_age": 30,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 101,
            "driving_experience_years": 8,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("regional_risk_index", form.errors)

    def test_driving_experience_exceeds_age(self):
        data = {
            "applicant_name": "Young Driver",
            "driver_age": 25,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 50,
            "driving_experience_years": 10,
        }
        form = ApplicationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_driving_experience_at_max_allowed(self):
        data = {
            "applicant_name": "Experienced Driver",
            "driver_age": 35,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 50,
            "driving_experience_years": 17,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())

    def test_form_excludes_calculated_fields(self):
        data = {
            "applicant_name": "Test User",
            "driver_age": 30,
            "vehicle_type": "sedan",
            "safety_rating": 3,
            "regional_risk_index": 50,
            "driving_experience_years": 8,
        }
        form = ApplicationForm(data)
        self.assertTrue(form.is_valid())
        self.assertNotIn("calculated_risk_score", form.fields)
        self.assertNotIn("initial_premium", form.fields)
        self.assertNotIn("final_premium", form.fields)
        self.assertNotIn("status", form.fields)
        self.assertNotIn("underwriter_notes", form.fields)


class RiskScoringServiceTestCase(TestCase):
    def setUp(self):
        self.application = Application.objects.create(
            applicant_name="Test Driver",
            driver_age=35,
            vehicle_type="sedan",
            safety_rating=4,
            regional_risk_index=50,
            driving_experience_years=10,
        )

    def test_missing_model_file_raises_error(self):
        """Test that missing model file raises FileNotFoundError with helpful message."""
        from underwriting.services import RiskScoringService

        with self.assertRaises(FileNotFoundError) as context:
            RiskScoringService()

        self.assertIn("risk_model.pkl", str(context.exception))
        self.assertIn("models", str(context.exception))

    def test_vehicle_type_encoding_mapping(self):
        """Test that all vehicle types are properly encoded."""
        from underwriting.services import RiskScoringService

        encoder = RiskScoringService.VEHICLE_TYPE_ENCODING
        self.assertEqual(len(encoder), 8)
        self.assertEqual(encoder["sedan"], 0)
        self.assertEqual(encoder["suv"], 1)
        self.assertEqual(encoder["truck"], 2)
        self.assertEqual(encoder["coupe"], 3)
        self.assertEqual(encoder["minivan"], 4)
        self.assertEqual(encoder["convertible"], 5)
        self.assertEqual(encoder["wagon"], 6)
        self.assertEqual(encoder["hatchback"], 7)

    def test_feature_extraction_with_valid_application(self):
        """Test feature extraction from a valid application."""
        from underwriting.services import RiskScoringService

        service = RiskScoringService.__new__(RiskScoringService)
        features = service._extract_features(self.application)

        self.assertEqual(len(features), 5)
        self.assertEqual(features[0], 35)  # driver_age
        self.assertEqual(features[1], 0)  # vehicle_type (sedan=0)
        self.assertEqual(features[2], 4)  # safety_rating
        self.assertEqual(features[3], 50)  # regional_risk_index
        self.assertEqual(features[4], 10)  # driving_experience_years

    def test_feature_extraction_with_different_vehicle_types(self):
        """Test feature extraction correctly encodes different vehicle types."""
        from underwriting.services import RiskScoringService

        service = RiskScoringService.__new__(RiskScoringService)

        vehicle_types = [
            ("sedan", 0),
            ("suv", 1),
            ("truck", 2),
            ("coupe", 3),
            ("minivan", 4),
            ("convertible", 5),
            ("wagon", 6),
            ("hatchback", 7),
        ]

        for vehicle_type, expected_encoding in vehicle_types:
            app = Application.objects.create(
                applicant_name=f"Test {vehicle_type}",
                driver_age=30,
                vehicle_type=vehicle_type,
                safety_rating=3,
                regional_risk_index=50,
                driving_experience_years=5,
            )
            features = service._extract_features(app)
            self.assertEqual(features[1], expected_encoding)

    def test_predict_with_none_application_raises_error(self):
        """Test that predict raises ValueError when application is None."""
        from underwriting.services import RiskScoringService

        service = RiskScoringService.__new__(RiskScoringService)

        with self.assertRaises(ValueError) as context:
            service.predict(None)

        self.assertIn("Application instance cannot be None", str(context.exception))

    def test_feature_extraction_with_missing_field_raises_error(self):
        """Test that feature extraction raises ValueError for missing required fields."""
        from underwriting.services import RiskScoringService

        service = RiskScoringService.__new__(RiskScoringService)

        # Create an object with missing driver_age field
        class InvalidApplication:
            pass

        invalid_app = InvalidApplication()

        with self.assertRaises(ValueError) as context:
            service._extract_features(invalid_app)

        self.assertIn("missing required field", str(context.exception))

    def test_feature_extraction_with_invalid_vehicle_type_raises_error(self):
        """Test that feature extraction raises ValueError for invalid vehicle type."""
        from underwriting.services import RiskScoringService

        service = RiskScoringService.__new__(RiskScoringService)

        # Create an application with invalid vehicle type
        class MockApplication:
            driver_age = 30
            vehicle_type = "invalid_type"
            safety_rating = 3
            regional_risk_index = 50
            driving_experience_years = 5

        mock_app = MockApplication()

        with self.assertRaises(ValueError) as context:
            service._extract_features(mock_app)

        self.assertIn("Invalid vehicle type", str(context.exception))


class PremiumCalculatorTestCase(TestCase):
    """Test cases for premium calculation functions."""

    # Tests for calculate_premium function

    def test_calculate_premium_with_typical_values(self):
        """Test calculate_premium with typical risk score and coverage limit."""
        risk_score = Decimal(50)
        coverage_limit = Decimal(10000)

        # Formula: 50 * 12 * (10000 / 1000) = 50 * 12 * 10 = 6000
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("6000.00"))
        self.assertEqual(premium.as_tuple().exponent, -2)  # Verify 2 decimal places

    def test_calculate_premium_with_minimum_risk_score(self):
        """Test calculate_premium with minimum risk score (0)."""
        risk_score = Decimal(0)
        coverage_limit = Decimal(10000)

        # Formula: 0 * 12 * (10000 / 1000) = 0
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("0.00"))

    def test_calculate_premium_with_maximum_risk_score(self):
        """Test calculate_premium with maximum risk score (100)."""
        risk_score = Decimal(100)
        coverage_limit = Decimal(10000)

        # Formula: 100 * 12 * (10000 / 1000) = 100 * 12 * 10 = 12000
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("12000.00"))

    def test_calculate_premium_with_small_coverage_limit(self):
        """Test calculate_premium with very small coverage limit."""
        risk_score = Decimal(50)
        coverage_limit = Decimal(100)

        # Formula: 50 * 12 * (100 / 1000) = 50 * 12 * 0.1 = 60
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("60.00"))

    def test_calculate_premium_with_decimal_precision(self):
        """Test calculate_premium maintains decimal precision."""
        risk_score = Decimal("33.33")
        coverage_limit = Decimal(7500)

        # Formula: 33.33 * 12 * (7500 / 1000) = 33.33 * 12 * 7.5 = 2999.70
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("2999.70"))

    def test_calculate_premium_risk_score_below_zero_raises_error(self):
        """Test calculate_premium raises ValueError when risk_score < 0."""
        with self.assertRaises(ValueError) as context:
            calculate_premium(Decimal(-1), Decimal(10000))

        self.assertIn("between 0 and 100", str(context.exception))

    def test_calculate_premium_risk_score_above_100_raises_error(self):
        """Test calculate_premium raises ValueError when risk_score > 100."""
        with self.assertRaises(ValueError) as context:
            calculate_premium(Decimal(101), Decimal(10000))

        self.assertIn("between 0 and 100", str(context.exception))

    def test_calculate_premium_coverage_limit_zero_raises_error(self):
        """Test calculate_premium raises ValueError when coverage_limit is 0."""
        with self.assertRaises(ValueError) as context:
            calculate_premium(Decimal(50), Decimal(0))

        self.assertIn("greater than 0", str(context.exception))

    def test_calculate_premium_coverage_limit_negative_raises_error(self):
        """Test calculate_premium raises ValueError when coverage_limit < 0."""
        with self.assertRaises(ValueError) as context:
            calculate_premium(Decimal(50), Decimal(-1000))

        self.assertIn("greater than 0", str(context.exception))

    def test_calculate_premium_none_risk_score_raises_type_error(self):
        """Test calculate_premium raises TypeError when risk_score is None."""
        with self.assertRaises(TypeError) as context:
            calculate_premium(None, Decimal(10000))

        self.assertIn("cannot be None", str(context.exception))

    def test_calculate_premium_none_coverage_limit_raises_type_error(self):
        """Test calculate_premium raises TypeError when coverage_limit is None."""
        with self.assertRaises(TypeError) as context:
            calculate_premium(Decimal(50), None)

        self.assertIn("cannot be None", str(context.exception))

    def test_calculate_premium_with_float_inputs(self):
        """Test calculate_premium accepts float inputs and converts to Decimal."""
        risk_score = 50.0
        coverage_limit = 10000.0

        # Should work and produce same result as Decimal inputs
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("6000.00"))

    def test_calculate_premium_with_int_inputs(self):
        """Test calculate_premium accepts int inputs and converts to Decimal."""
        risk_score = 50
        coverage_limit = 10000

        # Should work and produce same result as Decimal inputs
        premium = calculate_premium(risk_score, coverage_limit)

        self.assertEqual(premium, Decimal("6000.00"))

    # Tests for calculate_premium_with_overrides function

    def test_calculate_premium_with_overrides_typical_values(self):
        """Test calculate_premium_with_overrides with typical values."""
        base_premium = Decimal(1000)
        deductible = Decimal(500)
        risk_override_pct = Decimal(10)

        # deductible_factor = 1.0 - (500 - 250) / 1750 * 0.15
        #                   = 1.0 - 250/1750 * 0.15
        #                   = 1.0 - 0.02142857... = 0.97857142...
        # override_factor = 1.0 + (10 / 100) = 1.10
        # result = 1000 * 0.97857142... * 1.10 = 1076.43 (approx)

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        # More precise calculation using Decimal
        expected = Decimal("1076.43")
        self.assertEqual(premium, expected)

    def test_calculate_premium_with_overrides_minimum_deductible(self):
        """Test calculate_premium_with_overrides with minimum deductible (250)."""
        base_premium = Decimal(1000)
        deductible = Decimal(250)
        risk_override_pct = Decimal(0)

        # deductible_factor = 1.0 - (250 - 250) / 1750 * 0.15 = 1.0 - 0 = 1.0
        # override_factor = 1.0 + (0 / 100) = 1.0
        # result = 1000 * 1.0 * 1.0 = 1000

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        self.assertEqual(premium, Decimal("1000.00"))

    def test_calculate_premium_with_overrides_maximum_deductible(self):
        """Test calculate_premium_with_overrides with maximum deductible (2000)."""
        base_premium = Decimal(1000)
        deductible = Decimal(2000)
        risk_override_pct = Decimal(0)

        # deductible_factor = 1.0 - (2000 - 250) / 1750 * 0.15
        #                   = 1.0 - 1750/1750 * 0.15
        #                   = 1.0 - 0.15 = 0.85
        # override_factor = 1.0
        # result = 1000 * 0.85 * 1.0 = 850

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        self.assertEqual(premium, Decimal("850.00"))

    def test_calculate_premium_with_overrides_minimum_risk_override(self):
        """Test calculate_premium_with_overrides with minimum risk override (-25)."""
        base_premium = Decimal(1000)
        deductible = Decimal(250)
        risk_override_pct = Decimal(-25)

        # deductible_factor = 1.0
        # override_factor = 1.0 + (-25 / 100) = 0.75
        # result = 1000 * 1.0 * 0.75 = 750

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        self.assertEqual(premium, Decimal("750.00"))

    def test_calculate_premium_with_overrides_maximum_risk_override(self):
        """Test calculate_premium_with_overrides with maximum risk override (+25)."""
        base_premium = Decimal(1000)
        deductible = Decimal(250)
        risk_override_pct = Decimal(25)

        # deductible_factor = 1.0
        # override_factor = 1.0 + (25 / 100) = 1.25
        # result = 1000 * 1.0 * 1.25 = 1250

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        self.assertEqual(premium, Decimal("1250.00"))

    def test_calculate_premium_with_overrides_negative_risk_override(self):
        """Test calculate_premium_with_overrides with negative risk override."""
        base_premium = Decimal(1000)
        deductible = Decimal(500)
        risk_override_pct = Decimal(-10)

        # deductible_factor = 1.0 - 250/1750 * 0.15 ≈ 0.97857142...
        # override_factor = 1.0 + (-10 / 100) = 0.90
        # result ≈ 1000 * 0.97857142... * 0.90 ≈ 880.71

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        expected = Decimal("880.71")
        self.assertEqual(premium, expected)

    def test_calculate_premium_with_overrides_deductible_below_min_raises_error(self):
        """Test raises ValueError when deductible < 250."""
        with self.assertRaises(ValueError) as context:
            calculate_premium_with_overrides(Decimal(1000), Decimal(249), Decimal(0))

        self.assertIn("between 250 and 2000", str(context.exception))

    def test_calculate_premium_with_overrides_deductible_above_max_raises_error(self):
        """Test raises ValueError when deductible > 2000."""
        with self.assertRaises(ValueError) as context:
            calculate_premium_with_overrides(Decimal(1000), Decimal(2001), Decimal(0))

        self.assertIn("between 250 and 2000", str(context.exception))

    def test_calculate_premium_with_overrides_risk_override_below_min_raises_error(
        self,
    ):
        """Test raises ValueError when risk_override_pct < -25."""
        with self.assertRaises(ValueError) as context:
            calculate_premium_with_overrides(Decimal(1000), Decimal(500), Decimal(-26))

        self.assertIn("between -25 and 25", str(context.exception))

    def test_calculate_premium_with_overrides_risk_override_above_max_raises_error(
        self,
    ):
        """Test raises ValueError when risk_override_pct > 25."""
        with self.assertRaises(ValueError) as context:
            calculate_premium_with_overrides(Decimal(1000), Decimal(500), Decimal(26))

        self.assertIn("between -25 and 25", str(context.exception))

    def test_calculate_premium_with_overrides_none_base_premium_raises_type_error(self):
        """Test raises TypeError when base_premium is None."""
        with self.assertRaises(TypeError) as context:
            calculate_premium_with_overrides(None, Decimal(500), Decimal(0))

        self.assertIn("cannot be None", str(context.exception))

    def test_calculate_premium_with_overrides_none_deductible_raises_type_error(self):
        """Test raises TypeError when deductible is None."""
        with self.assertRaises(TypeError) as context:
            calculate_premium_with_overrides(Decimal(1000), None, Decimal(0))

        self.assertIn("cannot be None", str(context.exception))

    def test_calculate_premium_with_overrides_none_risk_override_raises_type_error(
        self,
    ):
        """Test raises TypeError when risk_override_pct is None."""
        with self.assertRaises(TypeError) as context:
            calculate_premium_with_overrides(Decimal(1000), Decimal(500), None)

        self.assertIn("cannot be None", str(context.exception))

    def test_calculate_premium_with_overrides_with_float_inputs(self):
        """Test calculate_premium_with_overrides accepts float inputs."""
        base_premium = 1000.0
        deductible = 500.0
        risk_override_pct = 10.0

        # Should work with float inputs
        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        expected = Decimal("1076.43")
        self.assertEqual(premium, expected)

    def test_calculate_premium_with_overrides_decimal_precision(self):
        """Test calculate_premium_with_overrides maintains decimal precision."""
        base_premium = Decimal("1234.56")
        deductible = Decimal(625)
        risk_override_pct = Decimal("5.5")

        # Calculate step by step
        # deductible_factor = 1.0 - (625 - 250) / 1750 * 0.15
        #                   = 1.0 - (375 / 1750 * 0.15)
        # override_factor = 1.0 + (5.5 / 100)
        # result = 1234.56 * deductible_factor * override_factor

        premium = calculate_premium_with_overrides(
            base_premium, deductible, risk_override_pct
        )

        # Verify it's properly formatted to 2 decimal places
        self.assertEqual(premium.as_tuple().exponent, -2)
