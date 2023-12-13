from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import answers, questions, tags, users


class UserCreationForm(forms.ModelForm):

    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    repeat_pass = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = users.User
        fields = ('email', 'avatar')

    def clean_repeat_pass(self):
        password = self.cleaned_data.get("password1")
        repeat_pass = self.cleaned_data.get("password2")
        if password and repeat_pass and password != repeat_pass:
            raise ValidationError("Passwords don't match")
        return repeat_pass

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = users.User
        fields = ('email', 'password', 'avatar', 'is_active', 'is_superuser')


class UserAdmin(BaseUserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'date_joined', 'is_superuser')
    list_filter = ('is_superuser')
    fieldsets = (
                (None, {'fields': ('username', 'email', 'password',
                                   'avatar', 'date_joined', 'is_active')}),
                ('Permissions', {'fields': ('is_superuser')}
                 ))

    add_fieldsets = (
                    (None, {'classes': ('wide'),
                    'fields': ('username', 'email', 'password1', 'password2', 'avatar')}
                    ))
    search_fields = ('email')
    ordering = ('username', 'email', 'is_superuser', 'avatar', 'date_joined', 'is_active')
    filter_horizontal = ()


admin.site.register(answers.Answer)
admin.site.register(questions.Question)
admin.site.register(tags.Tag)
admin.site.register(users.User, UserAdmin)
