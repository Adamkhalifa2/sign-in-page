# forms.py
from django import forms
from .models import Payment


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['phone_number']
