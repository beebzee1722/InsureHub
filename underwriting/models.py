from django.contrib.auth.models import User
from django.db import models


class Application(models.Model):
    STATUS_CHOICES = [
        ('flagged', 'Flagged'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    VEHICLE_TYPE_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('coupe', 'Coupe'),
        ('minivan', 'Minivan'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('hatchback', 'Hatchback'),
    ]

    applicant_name = models.CharField(max_length=100)
    driver_age = models.PositiveIntegerField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    safety_rating = models.PositiveIntegerField()
    regional_risk_index = models.PositiveIntegerField()
    driving_experience_years = models.PositiveIntegerField()

    calculated_risk_score = models.PositiveIntegerField(null=True, blank=True)
    initial_premium = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_premium = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='flagged')

    deductible_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    risk_override_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    underwriter_notes = models.TextField(blank=True)
    underwriter_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    decision_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Application'

    def __str__(self):
        return f"{self.applicant_name} - {self.get_status_display()}"
