from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class RegField:
    def validate(field_value):
        if not field_value:
            raise ValueError('Поле обязательно для заполнения!')

class UserCreating(BaseUserManager, RegField):

    def create_user(self, username, email, avatar, password):
        
        self.validate(username)
        self.validate(email)
        self.validate(password)

        user = self.model(username=username,
                          email=self.normalize_email(email),
                          avatar=avatar)

        user.set_password(password)
        user.save(using=self._db)
        return user

def photo_dir(inp, filename):
    return f'media/photos/{inp.id}/{filename}'

class User(AbstractUser):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'avatar']

    avatar = models.ImageField(upload_to=photo_dir,
                               blank=True,
                               null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    manager = UserCreating()
