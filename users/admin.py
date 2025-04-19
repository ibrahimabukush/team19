from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import LecturerProfile
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_student', 'is_lecturer', 'is_approved']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_student', 'is_lecturer', 'is_approved')}),
    )

admin.site.register(User, CustomUserAdmin)





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
