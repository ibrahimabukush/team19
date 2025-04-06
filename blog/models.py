from django.db import models

class ChatHistory(models.Model):
    username = models.CharField(max_length=100)
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"