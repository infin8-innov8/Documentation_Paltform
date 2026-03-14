from django import forms
from django.contrib.auth import authenticate

from django.contrib.auth import get_user_model

User = get_user_model()

class LoginForm(forms.Form):
    username_or_email = forms.CharField(label='Username or Email', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean(self):
        login_val = self.cleaned_data.get('username_or_email')
        password = self.cleaned_data.get('password')

        if login_val and password:
            # Check if user exists by email or username
            user_obj = User.objects.filter(email=login_val).first() or User.objects.filter(username=login_val).first()
            
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
            else:
                user = None
                
            if not user:
                raise forms.ValidationError('Invalid username/email or password.')
            if not user.is_active:
                raise forms.ValidationError('This account is inactive.')
            self.user_cache = user
            
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
