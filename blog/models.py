from django.db import models
from django.contrib.auth.models import User


class ChatHistory(models.Model):
    username = models.CharField(max_length=100)
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    

class StudentRequest(models.Model):
    username = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    request_type = models.CharField(max_length=255)
    text = models.TextField()
    attachment = models.FileField(upload_to='requests/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
def __str__(self):
        return f"{self.username} - {self.category} - {self.request_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

from django.db import models
from django.conf import settings

# class UserDocument(models.Model):
#     """Model to track documents saved to user profiles."""
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     document_type = models.CharField(max_length=100)
#     semester = models.CharField(max_length=50)
#     filename = models.CharField(max_length=255)
#     file_path = models.CharField(max_length=500)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"{self.document_type} - {self.user.username} - {self.semester}"

from datetime import timedelta
from django.utils import timezone

class AcademicRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('need_update', 'נדרש עדכון'),
        ('approved', 'מאושר'),
        ('rejected', 'נדחה'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    request_type = models.CharField(max_length=255)
    request_text = models.TextField()
    lecturer_note = models.TextField(blank=True, null=True)  # ✅ הערות המרצה
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    update_deadline = models.DateTimeField(blank=True, null=True)  # ✅ דדליין לעדכון

    def is_past_deadline(self):
        return self.update_deadline and timezone.now() > self.update_deadline

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.status}"
