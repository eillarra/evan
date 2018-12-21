from allauth.account.forms import SignupForm
from captcha.fields import ReCaptchaField
from django import forms
from django.conf import settings


class EvanSignupForm(SignupForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.DEBUG:
            self.fields['captcha'] = ReCaptchaField()
