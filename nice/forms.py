# forms.py
from django import forms
from .models import Payment, Profile


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['phone_number']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'location', 'phone_number', 'email']
