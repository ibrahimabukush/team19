# blog/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from users.models import Subject
class ScheduleRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('need_update', 'נדרש עדכון'),
        ('approved', 'מאושר'),
        ('rejected', 'נדחה'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('שינויי מערכת שעות', 'שינויי מערכת שעות'),
        ('בקשות הארכת זמן', 'בקשות הארכת זמן'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=255, choices=REQUEST_TYPE_CHOICES)
    request_text = models.TextField()
    lecturer_note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    review_started_at = models.DateTimeField(blank=True, null=True)
    update_requested_at = models.DateTimeField(blank=True, null=True)
    update_deadline = models.DateTimeField(blank=True, null=True)
    decision_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def is_past_deadline(self):
        return self.update_deadline and timezone.now() > self.update_deadline
    
    def __str__(self):
        return f"{self.student} - {self.request_type} - {self.status}"
from django.db import models
from django.utils import timezone
from django.conf import settings  # Import settings
from django.urls import reverse
from users.models import Subject

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    # Change this line to use your custom user model
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

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

class AcademicRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('need_update', 'נדרש עדכון'),
        ('approved', 'מאושר'),
        ('rejected', 'נדחה'),
    ]
    
    REQUEST_TYPES = [
        ('enrollment_confirmation', 'אישורי רישום או ציונים'),
        ('academic_appeal', 'ערעורים אקדמיים'),
        ('exam_review', 'בקשות לבדיקת מבחנים'),
        ('schedule_change', 'שינוי מערכת שעות'),
        ('administrative', 'בקשות מנהליות'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_requests')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_requests')
    subject = models.CharField(max_length=255)
    request_type = models.CharField(max_length=255)
    request_text = models.TextField()
    lecturer_note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    update_deadline = models.DateTimeField(blank=True, null=True)
    attachment = models.FileField(upload_to='request_attachments/', blank=True, null=True)

    def is_past_deadline(self):
        return self.update_deadline and timezone.now() > self.update_deadline

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.status}"
    

    