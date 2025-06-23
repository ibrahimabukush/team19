from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import LecturerProfile , Subject
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_student', 'is_lecturer','is_secretary', 'is_approved']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_student', 'is_lecturer', 'is_secretary','is_approved')}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'lecturer')
    list_filter = ('department', 'lecturer')
    search_fields = ('name', 'lecturer__username')
    ordering = ('name',)




class LecturerProfileInline(admin.StackedInline):
    model = LecturerProfile
    can_delete = False

class CustomUserAdmin(admin.ModelAdmin):
    inlines = (LecturerProfileInline,)
    list_display = ('username', 'email', 'get_subject')

    def get_subject(self, obj):
        return obj.lecturerprofile.subject
    get_subject.short_description = 'Subject'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
