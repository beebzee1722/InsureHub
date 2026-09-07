from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'driver_age', 'calculated_risk_score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('applicant_name',)
    readonly_fields = ('calculated_risk_score', 'created_at', 'updated_at', 'decision_timestamp')
