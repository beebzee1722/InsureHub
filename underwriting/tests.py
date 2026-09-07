from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .forms import ApplicationForm
from .models import Application
from .services import (
    calculate_premium,
    calculate_premium_with_overrides,
    categorize_status,
)


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


class STPEngineTestCase(TestCase):
    """Test cases for the STP Engine categorize_status function."""

    # Approved band tests (risk_score < 20)
    def test_categorize_status_approved_minimum(self):
        """Test categorize_status returns 'approved' for minimum score (0.0)."""
        result = categorize_status(0.0)
        self.assertEqual(result, "approved")

    def test_categorize_status_approved_near_boundary(self):
        """Test categorize_status returns 'approved' for score near boundary (19.99)."""
        result = categorize_status(19.99)
        self.assertEqual(result, "approved")

    def test_categorize_status_approved_mid_range(self):
        """Test categorize_status returns 'approved' for mid-range score (10.0)."""
        result = categorize_status(10.0)
        self.assertEqual(result, "approved")

    # Flagged band tests (20 <= risk_score <= 85)
    def test_categorize_status_flagged_at_lower_boundary(self):
        """Test categorize_status returns 'flagged' at lower boundary (20.0)."""
        result = categorize_status(20.0)
        self.assertEqual(result, "flagged")

    def test_categorize_status_flagged_just_above_lower_boundary(self):
        """Test categorize_status returns 'flagged' just above lower boundary (20.01)."""
        result = categorize_status(20.01)
        self.assertEqual(result, "flagged")

    def test_categorize_status_flagged_mid_range(self):
        """Test categorize_status returns 'flagged' for mid-range score (50.0)."""
        result = categorize_status(50.0)
        self.assertEqual(result, "flagged")

    def test_categorize_status_flagged_at_upper_boundary(self):
        """Test categorize_status returns 'flagged' at upper boundary (85.0)."""
        result = categorize_status(85.0)
        self.assertEqual(result, "flagged")

    def test_categorize_status_flagged_just_below_upper_boundary(self):
        """Test categorize_status returns 'flagged' just below upper boundary (84.99)."""
        result = categorize_status(84.99)
        self.assertEqual(result, "flagged")

    # Rejected band tests (risk_score > 85)
    def test_categorize_status_rejected_just_above_boundary(self):
        """Test categorize_status returns 'rejected' just above boundary (85.01)."""
        result = categorize_status(85.01)
        self.assertEqual(result, "rejected")

    def test_categorize_status_rejected_mid_range(self):
        """Test categorize_status returns 'rejected' for mid-range score (90.0)."""
        result = categorize_status(90.0)
        self.assertEqual(result, "rejected")

    def test_categorize_status_rejected_maximum(self):
        """Test categorize_status returns 'rejected' for maximum score (100.0)."""
        result = categorize_status(100.0)
        self.assertEqual(result, "rejected")

    # Edge cases and error handling
    def test_categorize_status_negative_risk_score_raises_error(self):
        """Test categorize_status raises ValueError for negative risk score."""
        with self.assertRaises(ValueError) as context:
            categorize_status(-1.0)
        self.assertIn("between 0 and 100", str(context.exception))

    def test_categorize_status_risk_score_above_100_raises_error(self):
        """Test categorize_status raises ValueError for risk score > 100."""
        with self.assertRaises(ValueError) as context:
            categorize_status(101.0)
        self.assertIn("between 0 and 100", str(context.exception))

    def test_categorize_status_invalid_type_string_raises_error(self):
        """Test categorize_status raises TypeError for string input."""
        with self.assertRaises(TypeError) as context:
            categorize_status("50")
        self.assertIn("must be a float", str(context.exception))

    def test_categorize_status_invalid_type_none_raises_error(self):
        """Test categorize_status raises TypeError for None input."""
        with self.assertRaises(TypeError) as context:
            categorize_status(None)
        self.assertIn("must be a float", str(context.exception))

    def test_categorize_status_int_input_accepted(self):
        """Test categorize_status accepts int input (should be converted to float)."""
        result = categorize_status(50)
        self.assertEqual(result, "flagged")

    def test_categorize_status_with_float_precision(self):
        """Test categorize_status handles float precision correctly."""
        # Test with a float that has many decimal places
        result = categorize_status(42.123456789)
        self.assertEqual(result, "flagged")


class HomeViewTestCase(TestCase):
    def test_home_view_returns_200(self):
        """Test home_view returns status 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_view_renders_home_template(self):
        """Test home_view renders home.html template."""
        response = self.client.get("/")
        self.assertTemplateUsed(response, "home.html")


class ApplicationFormViewTestCase(TestCase):
    def test_application_form_view_returns_200(self):
        """Test application_form_view returns status 200."""
        response = self.client.get("/applications/new/")
        self.assertEqual(response.status_code, 200)

    def test_application_form_view_renders_intake_form_template(self):
        """Test application_form_view renders intake/form.html template."""
        response = self.client.get("/applications/new/")
        self.assertTemplateUsed(response, "intake/form.html")

    def test_application_form_view_context_has_form_instance(self):
        """Test application_form_view context contains ApplicationForm instance."""
        response = self.client.get("/applications/new/")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ApplicationForm)


class URLResolutionTestCase(TestCase):
    def test_home_url_resolves(self):
        """Test home URL resolves to home_view."""
        from django.urls import resolve

        resolver = resolve("/")
        self.assertEqual(resolver.func.__name__, "home_view")

    def test_application_form_url_resolves(self):
        """Test application form URL resolves to application_form_view."""
        from django.urls import resolve

        resolver = resolve("/applications/new/")
        self.assertEqual(resolver.func.__name__, "application_form_view")

    def test_application_create_url_resolves(self):
        """Test application create URL resolves to application_create_view."""
        from django.urls import resolve

        resolver = resolve("/applications/create/")
        self.assertEqual(resolver.func.__name__, "application_create_view")

    def test_application_confirmation_url_resolves(self):
        """Test application confirmation URL resolves to application_confirmation_view."""
        from django.urls import resolve

        resolver = resolve("/applications/1/confirmation/")
        self.assertEqual(resolver.func.__name__, "application_confirmation_view")


class ApplicationCreateViewTestCase(TestCase):
    """Test cases for application_create_view (POST /applications/create/)."""

    def setUp(self):
        """Set up test data."""
        self.form_data = {
            "applicant_name": "John Doe",
            "driver_age": 35,
            "vehicle_type": "sedan",
            "safety_rating": 4,
            "regional_risk_index": 50,
            "driving_experience_years": 10,
        }

    def test_create_view_with_valid_form_redirects_to_confirmation(self):
        """Test valid form submission redirects to confirmation page."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 50.0
            mock_scorer_class.return_value = mock_scorer

            response = self.client.post("/applications/create/", self.form_data)

            # Verify application was created
            app = Application.objects.first()
            self.assertIsNotNone(app)
            self.assertEqual(app.applicant_name, "John Doe")

            # Verify redirect
            self.assertEqual(response.status_code, 302)
            self.assertTrue(
                response.url.endswith(f"/applications/{app.id}/confirmation/")
            )

    def test_create_view_saves_calculated_risk_score(self):
        """Test that calculated_risk_score is saved correctly."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 42.5
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.calculated_risk_score, 42)  # Rounded

    def test_create_view_saves_initial_premium(self):
        """Test that initial_premium is calculated and saved correctly."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 50.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            # Formula: 50 * 12 * (10000 / 1000) = 6000.00
            self.assertEqual(app.initial_premium, Decimal("6000.00"))

    def test_create_view_approved_status_for_low_risk(self):
        """Test status is 'approved' when risk score < 20."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 15.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.status, "approved")

    def test_create_view_flagged_status_for_medium_risk(self):
        """Test status is 'flagged' when 20 <= risk score <= 85."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 50.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.status, "flagged")

    def test_create_view_rejected_status_for_high_risk(self):
        """Test status is 'rejected' when risk score > 85."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 90.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.status, "rejected")

    def test_create_view_with_invalid_form_returns_200(self):
        """Test invalid form is re-rendered with errors (HTTP 200)."""
        invalid_data = self.form_data.copy()
        invalid_data["driver_age"] = 17  # Too young

        response = self.client.post("/applications/create/", invalid_data)

        # Should return 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intake/form.html")
        self.assertIn("form", response.context)
        self.assertFalse(response.context["form"].is_valid())

    def test_create_view_missing_required_field_returns_form_with_errors(self):
        """Test missing required field results in form with errors."""
        invalid_data = self.form_data.copy()
        del invalid_data["applicant_name"]

        response = self.client.post("/applications/create/", invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intake/form.html")
        self.assertIn("applicant_name", response.context["form"].errors)

    def test_create_view_risk_scorer_file_not_found_returns_500(self):
        """Test missing risk model file returns HTTP 500 with error.html."""
        from unittest.mock import patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer_class.side_effect = FileNotFoundError(
                "Risk model file not found"
            )

            response = self.client.post("/applications/create/", self.form_data)

            self.assertEqual(response.status_code, 500)
            self.assertTemplateUsed(response, "error.html")
            self.assertIn("error_message", response.context)

    def test_create_view_risk_scorer_value_error_returns_500(self):
        """Test ValueError during risk scoring returns HTTP 500."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.side_effect = ValueError("Invalid application data")
            mock_scorer_class.return_value = mock_scorer

            response = self.client.post("/applications/create/", self.form_data)

            self.assertEqual(response.status_code, 500)
            self.assertTemplateUsed(response, "error.html")

    def test_create_view_premium_calculation_error_returns_500(self):
        """Test error during premium calculation returns HTTP 500."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class, patch(
            "underwriting.views.calculate_premium"
        ) as mock_calc:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 50.0
            mock_scorer_class.return_value = mock_scorer
            mock_calc.side_effect = TypeError("Invalid premium arguments")

            response = self.client.post("/applications/create/", self.form_data)

            self.assertEqual(response.status_code, 500)
            self.assertTemplateUsed(response, "error.html")

    def test_create_view_database_save_error_returns_500(self):
        """Test database save error returns HTTP 500."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class, patch.object(
            Application, "save"
        ) as mock_save:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 50.0
            mock_scorer_class.return_value = mock_scorer
            mock_save.side_effect = Exception("Database error")

            response = self.client.post("/applications/create/", self.form_data)

            self.assertEqual(response.status_code, 500)
            self.assertTemplateUsed(response, "error.html")

    def test_create_view_non_post_request_redirects(self):
        """Test GET request redirects to application form."""
        response = self.client.get("/applications/create/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("/applications/new/"))

    def test_create_view_with_minimum_risk_score(self):
        """Test with minimum risk score (0)."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 0.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.calculated_risk_score, 0)
            self.assertEqual(app.status, "approved")

    def test_create_view_with_maximum_risk_score(self):
        """Test with maximum risk score (100)."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 100.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.calculated_risk_score, 100)
            self.assertEqual(app.status, "rejected")

    def test_create_view_with_boundary_risk_score_20(self):
        """Test with boundary risk score exactly 20 (flagged)."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 20.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.status, "flagged")

    def test_create_view_with_boundary_risk_score_85(self):
        """Test with boundary risk score exactly 85 (flagged)."""
        from unittest.mock import MagicMock, patch

        with patch("underwriting.views.RiskScoringService") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.predict.return_value = 85.0
            mock_scorer_class.return_value = mock_scorer

            self.client.post("/applications/create/", self.form_data)

            app = Application.objects.first()
            self.assertEqual(app.status, "flagged")


class ApplicationConfirmationViewTestCase(TestCase):
    """Test cases for application_confirmation_view."""

    def setUp(self):
        """Set up test data."""
        self.application = Application.objects.create(
            applicant_name="John Doe",
            driver_age=35,
            vehicle_type="sedan",
            safety_rating=4,
            regional_risk_index=50,
            driving_experience_years=10,
            calculated_risk_score=50,
            initial_premium="6000.00",
            status="flagged",
        )

    def test_confirmation_view_returns_200(self):
        """Test confirmation view returns HTTP 200."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertEqual(response.status_code, 200)

    def test_confirmation_view_renders_confirmation_template(self):
        """Test confirmation view renders confirmation.html template."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertTemplateUsed(response, "confirmation.html")

    def test_confirmation_view_context_has_application(self):
        """Test confirmation view context contains application object."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertIn("application", response.context)
        self.assertEqual(response.context["application"], self.application)

    def test_confirmation_view_displays_applicant_name(self):
        """Test confirmation page displays applicant name."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertContains(response, "John Doe")

    def test_confirmation_view_displays_risk_score(self):
        """Test confirmation page displays calculated risk score."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertContains(response, "50")

    def test_confirmation_view_displays_premium(self):
        """Test confirmation page displays initial premium."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertContains(response, "6000.00")

    def test_confirmation_view_displays_status(self):
        """Test confirmation page displays application status."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")
        self.assertContains(response, "Flagged")

    def test_confirmation_view_with_approved_application(self):
        """Test confirmation page with approved application."""
        app = Application.objects.create(
            applicant_name="Jane Smith",
            driver_age=28,
            vehicle_type="suv",
            safety_rating=5,
            regional_risk_index=30,
            driving_experience_years=5,
            calculated_risk_score=15,
            initial_premium="1800.00",
            status="approved",
        )

        response = self.client.get(f"/applications/{app.id}/confirmation/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "approved")
        self.assertContains(response, "Great news!")

    def test_confirmation_view_with_rejected_application(self):
        """Test confirmation page with rejected application."""
        app = Application.objects.create(
            applicant_name="Bob Johnson",
            driver_age=25,
            vehicle_type="truck",
            safety_rating=1,
            regional_risk_index=90,
            driving_experience_years=3,
            calculated_risk_score=95,
            initial_premium="11400.00",
            status="rejected",
        )

        response = self.client.get(f"/applications/{app.id}/confirmation/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rejected")
        self.assertContains(response, "Application Rejected")

    def test_confirmation_view_nonexistent_application_returns_404(self):
        """Test confirmation view with nonexistent application returns 404."""
        response = self.client.get("/applications/99999/confirmation/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "error.html")

    def test_confirmation_view_displays_all_details(self):
        """Test confirmation page displays all application details."""
        response = self.client.get(f"/applications/{self.application.id}/confirmation/")

        self.assertContains(response, "John Doe")  # applicant_name
        self.assertContains(response, "35")  # driver_age
        self.assertContains(response, "Sedan")  # vehicle_type
        self.assertContains(response, "4")  # safety_rating
        self.assertContains(response, "50")  # regional_risk_index or risk_score
        self.assertContains(response, "10")  # driving_experience_years
