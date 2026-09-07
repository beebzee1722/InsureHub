import logging
from decimal import Decimal

from django.shortcuts import redirect, render

from .forms import ApplicationForm
from .models import Application
from .services import (
    RiskScoringService,
    calculate_premium,
    categorize_status,
)

logger = logging.getLogger(__name__)

# Default coverage limit for initial premium calculation
DEFAULT_COVERAGE_LIMIT = Decimal(10000)


def home_view(request):
    return render(request, "home.html")


def application_form_view(request):
    form = ApplicationForm()
    return render(request, "intake/form.html", {"form": form})


def application_create_view(request):
    """Handle POST request to create an application with risk scoring."""
    if request.method != "POST":
        return redirect("application_form")

    form = ApplicationForm(request.POST)

    if not form.is_valid():
        # Re-render with form errors
        return render(request, "intake/form.html", {"form": form}, status=200)

    # Create application instance without saving
    application = form.save(commit=False)

    # Step 1: Call RiskScoringService.predict()
    try:
        scorer = RiskScoringService()
        risk_score = scorer.predict(application)
    except FileNotFoundError as e:
        logger.error(f"Risk model file not found: {e}")
        return render(request, "error.html", {"error_message": str(e)}, status=500)
    except ValueError as e:
        logger.error(f"Risk scoring error: {e}")
        return render(
            request,
            "error.html",
            {"error_message": "Error calculating risk score"},
            status=500,
        )

    # Step 2: Calculate premium
    try:
        initial_premium = calculate_premium(risk_score, DEFAULT_COVERAGE_LIMIT)
    except (ValueError, TypeError) as e:
        logger.error(f"Premium calculation error: {e}")
        return render(
            request,
            "error.html",
            {"error_message": "Error calculating premium"},
            status=500,
        )

    # Step 3: Categorize status based on risk score
    try:
        status = categorize_status(risk_score)
    except (ValueError, TypeError) as e:
        logger.error(f"Status categorization error: {e}")
        return render(
            request,
            "error.html",
            {"error_message": "Error categorizing application status"},
            status=500,
        )

    # Set calculated fields
    application.calculated_risk_score = round(risk_score)
    application.initial_premium = initial_premium
    application.status = status

    # Save to database
    try:
        application.save()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Database save error: {e}")
        return render(
            request,
            "error.html",
            {"error_message": "Error saving application to database"},
            status=500,
        )

    # Redirect to confirmation page
    return redirect("application_confirmation", application_id=application.id)


def application_confirmation_view(request, application_id):
    """Display confirmation for a saved application."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return render(
            request,
            "error.html",
            {"error_message": "Application not found"},
            status=404,
        )

    return render(request, "confirmation.html", {"application": application})
