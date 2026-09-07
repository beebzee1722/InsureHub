from django import forms
from django.core.exceptions import ValidationError
from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'applicant_name',
            'driver_age',
            'vehicle_type',
            'safety_rating',
            'regional_risk_index',
            'driving_experience_years',
        ]
        widgets = {
            'applicant_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
            }),
            'driver_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age (18-100)',
                'min': '18',
                'max': '100',
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'safety_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Safety Rating (1-5)',
                'min': '1',
                'max': '5',
            }),
            'regional_risk_index': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Regional Risk Index (1-100)',
                'min': '1',
                'max': '100',
            }),
            'driving_experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years of Driving Experience',
                'min': '0',
            }),
        }

    def clean_driver_age(self):
        driver_age = self.cleaned_data.get('driver_age')
        if driver_age is not None:
            if driver_age < 18 or driver_age > 100:
                raise ValidationError('Driver age must be between 18 and 100.')
        return driver_age

    def clean_safety_rating(self):
        safety_rating = self.cleaned_data.get('safety_rating')
        if safety_rating is not None:
            if safety_rating < 1 or safety_rating > 5:
                raise ValidationError('Safety rating must be between 1 and 5.')
        return safety_rating

    def clean_regional_risk_index(self):
        regional_risk_index = self.cleaned_data.get('regional_risk_index')
        if regional_risk_index is not None:
            if regional_risk_index < 1 or regional_risk_index > 100:
                raise ValidationError('Regional risk index must be between 1 and 100.')
        return regional_risk_index

    def clean(self):
        cleaned_data = super().clean()
        driver_age = cleaned_data.get('driver_age')
        driving_experience_years = cleaned_data.get('driving_experience_years')

        if driver_age is not None and driving_experience_years is not None:
            max_experience = driver_age - 18
            if driving_experience_years > max_experience:
                raise ValidationError(
                    'Driving experience cannot exceed years since age 18. '
                    f'Maximum experience for age {driver_age} is {max_experience} years.'
                )

        return cleaned_data
