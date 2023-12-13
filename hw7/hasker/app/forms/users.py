from django.contrib.auth.forms import UserCreationForm
from django.forms import PasswordInput, TextInput, EmailInput

from ..models.users import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'avatar')
        widgets = {
            'username': TextInput(
                attrs={'class': 'form-control-sm', 'placeholder': "Enter username"}),
            'password1': PasswordInput(render_value=False, attrs={
                'class': 'form-control', 'placeholder': "Enter password"}),
            'password2': PasswordInput(render_value=False, attrs={
                'class': 'form-control', 'placeholder': "Enter same password"}),
            'email': EmailInput(attrs={
                'class': 'form-control', 'placeholder': "Enter your email"})
        }
