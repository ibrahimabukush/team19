# blog/admin.py
from django.contrib import admin
from .models import Post, ChatHistory, StudentRequest, AcademicRequest, ScheduleRequest

# Unregister if already registered and register again
admin.site.unregister(ChatHistory) if admin.site.is_registered(ChatHistory) else None
admin.site.unregister(Post) if admin.site.is_registered(Post) else None
admin.site.unregister(StudentRequest) if admin.site.is_registered(StudentRequest) else None
admin.site.unregister(AcademicRequest) if admin.site.is_registered(AcademicRequest) else None
admin.site.unregister(ScheduleRequest) if admin.site.is_registered(ScheduleRequest) else None

# Now register the models
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted')
    list_filter = ('date_posted', 'author')
    search_fields = ('title', 'content')

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('username', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('username', 'message', 'reply')
    readonly_fields = ('timestamp',)

@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'category', 'request_type', 'created_at')
    list_filter = ('category', 'request_type', 'created_at')
    search_fields = ('username', 'text')
    readonly_fields = ('created_at',)

@admin.register(AcademicRequest)
class AcademicRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'assigned_to', 'subject', 'request_type', 'status', 'created_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('student__username', 'subject', 'request_text')
    ordering = ('-created_at',)

@admin.register(ScheduleRequest)
class ScheduleRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'request_type', 'status', 'created_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('student__username', 'request_text')
    readonly_fields = ('created_at',)