from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('sw_engineering', 'Software Engineering'),
        ('computer_science', 'Computer Science'),
        ('electronic_engineering', 'Electronic Engineering'),
    ]
    
    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
        ('5', 'Fifth Year'),
    ]
    
    is_student = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)
    is_secretary = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    year = models.CharField(max_length=1, choices=YEAR_CHOICES, blank=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics', null=True, blank=True)


    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)



class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.subject}"
class Secretary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    office_location = models.CharField(max_length=100)
    phone_extension = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.user.username} - {self.user.department}"
    
    class Meta:
        verbose_name_plural = "Secretaries"
class Subject(models.Model):
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=50, choices=User.DEPARTMENT_CHOICES)
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        limit_choices_to={'is_lecturer': True},
        related_name='subjects'
    )
    
    def __str__(self):
        return f"{self.name} - {self.lecturer.username}"
    
    class Meta:
        unique_together = ('name', 'lecturer')