# blog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Post, ChatHistory, AcademicRequest, 
    ScheduleRequest, ErrorReport, ErrorReportComment, PersonalRequest
)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted')
    list_filter = ('date_posted', 'author')
    search_fields = ('title', 'content')
    ordering = ('-date_posted',)

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('username', 'timestamp', 'message_preview')
    list_filter = ('timestamp',)
    search_fields = ('username', 'message', 'reply')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'

@admin.register(AcademicRequest)
class AcademicRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'subject', 'request_type', 'status', 'created_at', 
        'is_past_deadline', 'secretary_note', 'lecturer_note', 
        'lecturer_file_status', 'secretary_file_status'
    )
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('student__username', 'subject', 'request_text')
    readonly_fields = ('created_at', 'lecturer_file_uploaded_at', 'secretary_file_uploaded_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('student', 'subject', 'request_type', 'request_text', 'status')
        }),
        ('Notes', {
            'fields': ('lecturer_note', 'secretary_note')
        }),
        ('Files - Lecturer', {
            'fields': ('lecturer_file', 'lecturer_file_name', 'lecturer_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Files - Secretary', {
            'fields': ('secretary_file', 'secretary_file_name', 'secretary_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'update_deadline'),
            'classes': ('collapse',)
        })
    )
    
    def is_past_deadline(self, obj):
        return obj.is_past_deadline()
    is_past_deadline.boolean = True
    is_past_deadline.short_description = 'Past Deadline'
    
    def lecturer_file_status(self, obj):
        if obj.lecturer_file:
            file_url = reverse('download_file', args=[obj.id, 'lecturer'])
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">📎 {}</a>',
                file_url,
                obj.lecturer_file_name or 'קובץ מרצה'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    lecturer_file_status.short_description = 'קובץ מרצה'
    
    def secretary_file_status(self, obj):
        if obj.secretary_file:
            file_url = reverse('download_file', args=[obj.id, 'secretary'])
            return format_html(
                '<a href="{}" target="_blank" style="color: blue;">📎 {}</a>',
                file_url,
                obj.secretary_file_name or 'קובץ מזכירות'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    secretary_file_status.short_description = 'קובץ מזכירות'

@admin.register(ScheduleRequest)
class ScheduleRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'subject', 'request_type', 'status', 'created_at', 
        'is_past_deadline', 'secretary_note', 'lecturer_note',
        'lecturer_file_status', 'secretary_file_status'
    )
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('student__username', 'subject', 'request_text')
    readonly_fields = ('created_at', 'lecturer_file_uploaded_at', 'secretary_file_uploaded_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('student', 'subject', 'request_type', 'request_text', 'status')
        }),
        ('Notes', {
            'fields': ('lecturer_note', 'secretary_note')
        }),
        ('Files - Lecturer', {
            'fields': ('lecturer_file', 'lecturer_file_name', 'lecturer_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Files - Secretary', {
            'fields': ('secretary_file', 'secretary_file_name', 'secretary_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'update_deadline'),
            'classes': ('collapse',)
        })
    )
    
    def is_past_deadline(self, obj):
        return obj.is_past_deadline()
    is_past_deadline.boolean = True
    is_past_deadline.short_description = 'Past Deadline'
    
    def lecturer_file_status(self, obj):
        if obj.lecturer_file:
            file_url = reverse('download_file', args=[obj.id, 'lecturer'])
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">📎 {}</a>',
                file_url,
                obj.lecturer_file_name or 'קובץ מרצה'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    lecturer_file_status.short_description = 'קובץ מרצה'
    
    def secretary_file_status(self, obj):
        if obj.secretary_file:
            file_url = reverse('download_file', args=[obj.id, 'secretary'])
            return format_html(
                '<a href="{}" target="_blank" style="color: blue;">📎 {}</a>',
                file_url,
                obj.secretary_file_name or 'קובץ מזכירות'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    secretary_file_status.short_description = 'קובץ מזכירות'

@admin.register(ErrorReport)
class ErrorReportAdmin(admin.ModelAdmin):
    list_display = (
        'reporter_name', 'error_type', 'priority', 'status', 
        'assigned_to', 'created_at', 'days_since_created'
    )
    list_filter = ('status', 'priority', 'error_type', 'created_at', 'assigned_to')
    search_fields = ('reporter_name', 'reporter_email', 'description')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'days_since_created')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Reporter Information', {
            'fields': ('reporter_user', 'reporter_name', 'reporter_email')
        }),
        ('Error Details', {
            'fields': ('error_type', 'priority', 'description', 'attachment')
        }),
        ('Technical Information', {
            'fields': ('user_agent', 'ip_address', 'page_url'),
            'classes': ('collapse',)
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to', 'admin_notes', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    
    def days_since_created(self, obj):
        return obj.days_since_created()
    days_since_created.short_description = 'Days Since Created'

@admin.register(ErrorReportComment)
class ErrorReportCommentAdmin(admin.ModelAdmin):
    list_display = ('error_report', 'author', 'created_at', 'is_internal', 'comment_preview')
    list_filter = ('is_internal', 'created_at', 'author')
    search_fields = ('comment', 'error_report__reporter_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'

@admin.register(PersonalRequest)
class PersonalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'request_type_display', 'status', 'created_at', 'updated_at',
        'secretary_note', 'lecturer_note', 'lecturer_file_status', 'secretary_file_status'
    )
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('student__username', 'request_text')
    readonly_fields = ('created_at', 'updated_at', 'lecturer_file_uploaded_at', 'secretary_file_uploaded_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('student', 'request_type', 'request_text', 'status')
        }),
        ('Notes', {
            'fields': ('lecturer_note', 'secretary_note')
        }),
        ('Files - Lecturer', {
            'fields': ('lecturer_file', 'lecturer_file_name', 'lecturer_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Files - Secretary', {
            'fields': ('secretary_file', 'secretary_file_name', 'secretary_file_uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'update_deadline'),
            'classes': ('collapse',)
        })
    )
    
    def request_type_display(self, obj):
        return obj.get_request_type_display()
    request_type_display.short_description = 'Request Type'
    
    def lecturer_file_status(self, obj):
        if obj.lecturer_file:
            file_url = reverse('download_file', args=[obj.id, 'lecturer'])
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">📎 {}</a>',
                file_url,
                obj.lecturer_file_name or 'קובץ מרצה'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    lecturer_file_status.short_description = 'קובץ מרצה'
    
    def secretary_file_status(self, obj):
        if obj.secretary_file:
            file_url = reverse('download_file', args=[obj.id, 'secretary'])
            return format_html(
                '<a href="{}" target="_blank" style="color: blue;">📎 {}</a>',
                file_url,
                obj.secretary_file_name or 'קובץ מזכירות'
            )
        return format_html('<span style="color: gray;">❌ אין קובץ</span>')
    secretary_file_status.short_description = 'קובץ מזכירות'