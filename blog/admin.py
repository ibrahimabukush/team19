from django.contrib import admin
from .models import ChatHistory
from .models import StudentRequest
@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('username', 'message', 'reply', 'timestamp')
    search_fields = ('username', 'message', 'reply')
    list_filter = ('timestamp',)


from django.contrib import admin
from .models import UserDocument

class UserDocumentAdmin(admin.ModelAdmin):
    # Change this:
    # list_display = ['username', 'document_type', 'created_at']
    
    # To this:
    list_display = ['get_username', 'document_type', 'created_at']
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

admin.site.register(UserDocument, UserDocumentAdmin)

@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'category', 'request_type', 'created_at')
    search_fields = ('username', 'request_type', 'category')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)
   