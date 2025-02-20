from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):  
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='customer')

    def __str__(self):
        return self.username