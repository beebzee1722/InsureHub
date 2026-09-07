import os
from pathlib import Path

import joblib
from django.conf import settings


class RiskScoringService:
    """Service for scoring insurance application risk using a pre-trained ML model."""

    # Vehicle type encoding mapping (based on Application.VEHICLE_TYPE_CHOICES order)
    VEHICLE_TYPE_ENCODING = {  # noqa: RUF012
        "sedan": 0,
        "suv": 1,
        "truck": 2,
        "coupe": 3,
        "minivan": 4,
        "convertible": 5,
        "wagon": 6,
        "hatchback": 7,
    }

    def __init__(self):
        """Initialize the service by loading the pre-trained model.

        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        model_path = self._get_model_path()

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Risk model file not found at {model_path}. "
                "Please ensure the pre-trained model is available at models/risk_model.pkl"
            )

        self.model = joblib.load(model_path)

    def _get_model_path(self):
        """Get the absolute path to the model file relative to Django project root.

        Returns:
            str: Absolute path to the risk_model.pkl file.
        """
        # Get Django project root
        project_root = Path(settings.BASE_DIR).parent
        model_path = project_root / "models" / "risk_model.pkl"
        return str(model_path)

    def predict(self, application):
        """Predict risk score for an insurance application.

        Args:
            application: Application model instance with required fields:
                - driver_age
                - vehicle_type
                - safety_rating
                - regional_risk_index
                - driving_experience_years

        Returns:
            float: Risk score between 0 and 100.

        Raises:
            ValueError: If application is invalid or missing required fields.
        """
        if not application:
            raise ValueError("Application instance cannot be None")

        # Extract and encode features in consistent order
        features = self._extract_features(application)

        # Use model to predict risk score
        risk_score = self.model.predict([features])[0]

        # Ensure score is within 0-100 range
        risk_score = max(0.0, min(100.0, float(risk_score)))

        return risk_score

    def _extract_features(self, application):
        """Extract and encode features from an application for model prediction.

        Args:
            application: Application model instance.

        Returns:
            list: Ordered feature list for model input.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        try:
            driver_age = application.driver_age
            vehicle_type = application.vehicle_type
            safety_rating = application.safety_rating
            regional_risk_index = application.regional_risk_index
            driving_experience_years = application.driving_experience_years
        except AttributeError as e:
            raise ValueError(f"Application is missing required field: {e}")

        # Encode vehicle type
        if vehicle_type not in self.VEHICLE_TYPE_ENCODING:
            raise ValueError(
                f"Invalid vehicle type: {vehicle_type}. "
                f"Must be one of {list(self.VEHICLE_TYPE_ENCODING.keys())}"
            )

        vehicle_type_encoded = self.VEHICLE_TYPE_ENCODING[vehicle_type]

        # Return features in consistent order
        return [
            driver_age,
            vehicle_type_encoded,
            safety_rating,
            regional_risk_index,
            driving_experience_years,
        ]
