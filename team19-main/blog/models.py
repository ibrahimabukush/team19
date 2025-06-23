# blog/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from users.models import Subject
import os

def lecturer_upload_path(instance, filename):
    """Generate upload path for lecturer files"""
    return f'lecturer_files/{instance.id}/{filename}'

def secretary_upload_path(instance, filename):
    """Generate upload path for secretary files"""
    return f'secretary_files/{instance.id}/{filename}'

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
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedule_requests'  # changed here
    )    
    lecturer_file = models.FileField(
        upload_to=lecturer_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המרצה"
    )
    
    secretary_file = models.FileField(
        upload_to=secretary_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המזכירות"
    )
    
    lecturer_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמרצה"
    )
    
    secretary_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמזכירות"
    )
    
    lecturer_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המרצה העלה את הקובץ"
    )
    
    secretary_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המזכירות העלתה את הקובץ"
    )

    subject = models.CharField(max_length=255)
    request_type = models.CharField(max_length=255, choices=REQUEST_TYPE_CHOICES)
    request_text = models.TextField()
    lecturer_note = models.TextField(blank=True, null=True, help_text="הערות מהמרצה")
    secretary_note = models.TextField(blank=True, null=True, help_text="הערות מהמזכירות")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    update_deadline = models.DateTimeField(blank=True, null=True)
    attachment = models.FileField(upload_to='schedule_attachments/', blank=True, null=True)

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


class AcademicRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('need_update', 'נדרש עדכון'),
        ('approved', 'מאושר'),
        ('rejected', 'נדחה'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('enrollment_confirmation', 'אישורי רישום או ציונים'),
        ('academic_appeal', 'ערעורים אקדמיים'),
        ('exam_review', 'בקשות לבדיקת מבחנים'),
        ('schedule_change', 'שינוי מערכת שעות'),
        ('administrative', 'בקשות מנהליות'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='academic_requests'  # changed here
    )    # assigned_to = models.ForeignKey(
    #     settings.AUTH_USER_MODEL, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True,
    #     related_name='assigned_requests'
    # )  
    lecturer_file = models.FileField(
        upload_to=lecturer_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המרצה"
    )
    
    secretary_file = models.FileField(
        upload_to=secretary_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המזכירות"
    )
    
    lecturer_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמרצה"
    )
    
    secretary_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמזכירות"
    )
    
    lecturer_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המרצה העלה את הקובץ"
    )
    
    secretary_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המזכירות העלתה את הקובץ"
    )
    subject = models.CharField(max_length=255)
    request_type = models.CharField(max_length=255, choices=REQUEST_TYPE_CHOICES)
    request_text = models.TextField()
    lecturer_note = models.TextField(blank=True, null=True, help_text="הערות מהמרצה")
    secretary_note = models.TextField(blank=True, null=True, help_text="הערות מהמזכירות")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    update_deadline = models.DateTimeField(blank=True, null=True)
    attachment = models.FileField(upload_to='request_attachments/', blank=True, null=True)

    def is_past_deadline(self):
        return self.update_deadline and timezone.now() > self.update_deadline

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.status}"
    
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatHistory(models.Model):
    username = models.CharField(max_length=150)
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.username}: {self.message[:50]}..."
    
from django.db import models
from django.utils import timezone
from django.conf import settings

class ErrorReport(models.Model):
    ERROR_TYPE_CHOICES = [
        ('syntax', 'שגיאת תחביר (Syntax)'),
        ('logic', 'שגיאה לוגית'),
        ('runtime', 'שגיאת ריצה'),
        ('ui', 'בעיה בממשק משתמש (UI/UX)'),
        ('performance', 'בעיית ביצועים'),
        ('login', 'בעיית התחברות (לא נכנס למערכת)'),
        ('notification', 'התראות לא נשלחות'),
        ('other', 'אחר'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'נמוכה (לא מפריעה לעבודה)'),
        ('medium', 'בינונית (מפריעה חלקית)'),
        ('high', 'גבוהה (מונע עבודה)'),
        ('critical', 'דחוף! (המערכת לא עובדת)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('resolved', 'נפתר'),
        ('closed', 'סגור'),
    ]
    
    # Reporter information
    reporter_name = models.CharField(max_length=100, verbose_name='שם מלא')
    reporter_email = models.EmailField(verbose_name='אימייל')
    
    # Error details
    error_type = models.CharField(
        max_length=20, 
        choices=ERROR_TYPE_CHOICES, 
        verbose_name='סוג השגיאה'
    )
    error_description = models.TextField(verbose_name='תיאור השגיאה')
    error_media = models.FileField(
        upload_to='error_reports/', 
        blank=True, 
        null=True, 
        verbose_name='תיעוד השגיאה'
    )
    
    # Priority and status
    urgency = models.CharField(
        max_length=10, 
        choices=URGENCY_CHOICES, 
        default='medium',
        verbose_name='דחיפות הטיפול'
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='סטטוס'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name='תאריך יצירה')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='תאריך עדכון')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='תאריך פתרון')
    
    # Technical team response
    admin_notes = models.TextField(blank=True, verbose_name='הערות צוות טכני')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        verbose_name='מוקצה ל'
    )
    
    class Meta:
        verbose_name = 'דיווח שגיאה'
        verbose_name_plural = 'דיווחי שגיאות'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reporter_name} - {self.get_error_type_display()} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

# In models.py
class PersonalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ממתין'),
        ('in_progress', 'בטיפול'),
        ('need_update', 'נדרש עדכון'),
        ('approved', 'אושר'),
        ('rejected', 'נדחה'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('recommendation_letter', 'בקשה למכתבי המלצה'),
        ('personal_details_update', 'עדכון פרטים אישיים'),
        ('certificates_confirmations', 'בקשת תעודות ואישורים'),
        ('scholarships_financial_aid', 'בקשות מלגות וסיוע כלכלי'),
        ('academic_status_change', 'בקשת שינוי סטטוס אקדמי'),
        ('general_manager_inquiry', 'פניה כללית למנהל'),
    ]
    lecturer_file = models.FileField(
        upload_to=lecturer_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המרצה"
    )
    
    secretary_file = models.FileField(
        upload_to=secretary_upload_path, 
        null=True, 
        blank=True,
        help_text="קובץ שמועלה על ידי המזכירות"
    )
    
    lecturer_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמרצה"
    )
    
    secretary_file_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="שם המקורי של הקובץ מהמזכירות"
    )
    
    lecturer_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המרצה העלה את הקובץ"
    )
    
    secretary_file_uploaded_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="מתי המזכירות העלתה את הקובץ"
    )
    lecturer_note = models.TextField(blank=True, null=True, help_text="הערות מהמרצה")
    secretary_note = models.TextField(blank=True, null=True, help_text="הערות מהמזכירות")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_requests')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    request_text = models.TextField()
    attachment = models.FileField(upload_to='personal_requests/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "בקשה אישית"
        verbose_name_plural = "בקשות אישיות"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.student.username}"
    
    # Add these classes to your existing blog/models.py file

class ErrorReport(models.Model):
    """Model for storing error reports submitted by users"""
    
    ERROR_TYPE_CHOICES = [
        ('syntax', 'שגיאת תחביר (Syntax)'),
        ('logic', 'שגיאה לוגית'),
        ('runtime', 'שגיאת ריצה'),
        ('ui', 'בעיה בממשק משתמש (UI/UX)'),
        ('performance', 'בעיית ביצועים'),
        ('login', 'בעיית התחברות'),
        ('notification', 'התראות לא נשלחות'),
        ('database', 'בעיית מסד נתונים'),
        ('security', 'בעיית אבטחה'),
        ('other', 'אחר'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'נמוכה - לא דחוף'),
        ('medium', 'בינונית - יש זמן'),
        ('high', 'גבוהה - דחוף'),
        ('critical', 'קריטי - חוסם עבודה'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'חדש'),
        ('in_progress', 'בטיפול'),
        ('resolved', 'נפתר'),
        ('closed', 'סגור'),
        ('duplicate', 'כפילות'),
        ('invalid', 'לא תקף'),
    ]
    
    # Reporter Information
    reporter_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_error_reports',
        verbose_name='משתמש מדווח'
    )
    reporter_name = models.CharField(
        max_length=100,
        verbose_name='שם המדווח'
    )
    reporter_email = models.EmailField(
        verbose_name='אימייל המדווח'
    )
    
    # Error Details
    error_type = models.CharField(
        max_length=20,
        choices=ERROR_TYPE_CHOICES,
        verbose_name='סוג השגיאה'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='עדיפות'
    )
    description = models.TextField(
        verbose_name='תיאור השגיאה'
    )
    
    # Technical Information
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='כתובת IP'
    )
    page_url = models.URLField(
        blank=True,
        max_length=500,
        verbose_name='URL של הדף'
    )
    
    # Attachments
    attachment = models.FileField(
        upload_to='error_reports/',
        null=True,
        blank=True,
        verbose_name='קובץ מצורף'
    )
    
    # Status and Management
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='סטטוס'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True},
        related_name='assigned_error_reports',
        verbose_name='מוקצה ל'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='תאריך יצירה'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='תאריך עדכון אחרון'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='תאריך פתרון'
    )
    
    # Admin Notes
    admin_notes = models.TextField(
        blank=True,
        verbose_name='הערות מנהל'
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name='הערות פתרון'
    )
    
    class Meta:
        verbose_name = 'דיווח שגיאה'
        verbose_name_plural = 'דיווחי שגיאות'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_error_type_display()} - {self.reporter_name} ({self.get_status_display()})"
    
    def get_error_type_hebrew(self):
        return self.get_error_type_display()
    
    def get_priority_hebrew(self):
        return self.get_priority_display()
    
    def get_status_hebrew(self):
        return self.get_status_display()
    
    def is_critical(self):
        return self.priority == 'critical'
    
    def is_resolved(self):
        return self.status in ['resolved', 'closed']
    
    def days_since_created(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).days
    
    def mark_as_resolved(self, user=None, notes=''):
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.assigned_to = user
        if notes:
            self.resolution_notes = notes
        self.save()

# Helper function to get file extension icon
def get_file_icon(filename):
    """Return appropriate icon based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        '.pdf': 'fas fa-file-pdf',
        '.doc': 'fas fa-file-word',
        '.docx': 'fas fa-file-word',
        '.xls': 'fas fa-file-excel',
        '.xlsx': 'fas fa-file-excel',
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.png': 'fas fa-file-image',
        '.txt': 'fas fa-file-alt',
    }
    return icons.get(ext, 'fas fa-file')
class ErrorReportComment(models.Model):
    """Model for comments/updates on error reports"""
    
    error_report = models.ForeignKey(
        ErrorReport,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='דיווח שגיאה'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='כותב התגובה'
    )
    comment = models.TextField(
        verbose_name='תגובה'
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name='תגובה פנימית'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='תאריך יצירה'
    )
    
    class Meta:
        verbose_name = 'תגובה על דיווח שגיאה'
        verbose_name_plural = 'תגובות על דיווחי שגיאות'
        ordering = ['created_at']
    
    def __str__(self):
        return f"תגובה של {self.author.username} על {self.error_report}"


# Utility function for error report statistics
def get_error_report_stats():
    """Get statistics about error reports"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total': ErrorReport.objects.count(),
        'new': ErrorReport.objects.filter(status='new').count(),
        'in_progress': ErrorReport.objects.filter(status='in_progress').count(),
        'resolved': ErrorReport.objects.filter(status='resolved').count(),
        'critical': ErrorReport.objects.filter(priority='critical').count(),
        'this_week': ErrorReport.objects.filter(created_at__gte=week_ago).count(),
        'this_month': ErrorReport.objects.filter(created_at__gte=month_ago).count(),
        'by_type': ErrorReport.objects.values('error_type').annotate(count=Count('id')),
        'by_priority': ErrorReport.objects.values('priority').annotate(count=Count('id')),
    }
    
    return stats

