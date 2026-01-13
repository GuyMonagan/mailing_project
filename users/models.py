from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None  # Удаляем username
    email = models.EmailField(unique=True, verbose_name="Email")

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Аватар")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    country = models.CharField(max_length=100, blank=True, verbose_name="Страна")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
