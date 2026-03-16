from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Profile


class UserRegisterForm(UserCreationForm):
    CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
    ]
    role = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']


class UserUpdateForm(UserChangeForm):
    password = None # Will make a separate password change form

    class Meta:
        model = User
        fields = ['username', 'email']
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role']