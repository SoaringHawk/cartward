from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.contrib.auth.forms import AuthenticationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=15, required=True, help_text="Username limited to 15 characters")

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']


class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=15, required=True, help_text="Username limited to 15 characters")

    class Meta:
        model = User
        fields = ['username']

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=100, required=False)

    class Meta:
        model = Profile
        fields = ['email']


class ProfileRegisterForm(forms.ModelForm):
    email = forms.EmailField(max_length=100, required=False)

    class Meta:
        model = Profile
        fields = ['email']

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class ChangeEmail(forms.Form):
    email1 = forms.EmailField(label=u'Type new Email')
    email2 = forms.EmailField(label=u'Type Email again')