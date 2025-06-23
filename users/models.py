# users/models.py - UPDATED MODEL
from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image

class User(AbstractUser):
    # Updated department choices to match your system
    DEPARTMENT_CHOICES = [
        ('מדעי המחשב', 'מדעי המחשב'),
        ('הנדסת תוכנה', 'הנדסת תוכנה'),
        ('הנדסת אלקטרוניקה', 'הנדסת אלקטרוניקה'),
        # Keep English codes for compatibility
        # ('sw_engineering', 'Software Engineering'),
        # ('computer_science', 'Computer Science'),
        # ('electronic_engineering', 'Electronic Engineering'),
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
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    year = models.CharField(max_length=1, choices=YEAR_CHOICES, blank=True)
    
    # Add custom full_name field (Option 1 - Recommended)
    full_name = models.CharField(max_length=150, blank=True, help_text="שם מלא")
    
    def get_full_name(self):
        """
        Return the full name for the user.
        If full_name is set, use it. Otherwise, combine first_name and last_name.
        """
        if self.full_name:
            return self.full_name
        return super().get_full_name()
    
    def save(self, *args, **kwargs):
        # If full_name is provided but first_name/last_name are empty, try to split
        if self.full_name and not self.first_name and not self.last_name:
            name_parts = self.full_name.strip().split(' ', 1)
            self.first_name = name_parts[0] if name_parts else ''
            self.last_name = name_parts[1] if len(name_parts) > 1 else ''
        # If first_name/last_name are provided but full_name is empty, combine them
        elif not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        super().save(*args, **kwargs)

from django.db import models
from .models import User  # אם בתוך אותו קובץ

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('secretary', 'Secretary'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')  # ← חדש

    def __str__(self):
        return f'{self.user.username} Profile'


class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, blank=True)  # Make it optional

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.subject}"

class Secretary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    office_location = models.CharField(max_length=100)
    phone_extension = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.full_name} - {self.user.department}"

    class Meta:
        verbose_name_plural = "Secretaries"

class Subject(models.Model):
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=50, choices=User.DEPARTMENT_CHOICES)
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_lecturer': True},
        related_name='taught_subjects'  # Changed from 'subjects'
    )

    def __str__(self):
        return f"{self.name} - {self.lecturer.full_name}"

    class Meta:
        unique_together = ('name', 'lecturer')



        