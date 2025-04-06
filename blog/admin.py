from django.contrib import admin
from .models import ChatHistory

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('username', 'message', 'reply', 'timestamp')
    search_fields = ('username', 'message', 'reply')
    list_filter = ('timestamp',)