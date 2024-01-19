from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'exampleInputtext1'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'exampleInputPassword1'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'exampleInputPassword2'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'exampleInputtext1'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'exampleInputPassword1'}))
