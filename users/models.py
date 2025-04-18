from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics', null=True, blank=True)


    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)



class LecturerProfile(models.Model):
       user = models.OneToOneField(User, on_delete=models.CASCADE)
       subject = models.CharField(max_length=255)  # e.g., "Algorithms"

def __str__(self):
        return f"{self.user.get_full_name()} - {self.subject}"
