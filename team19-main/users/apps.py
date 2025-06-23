from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # import users.signals  ← This was causing the error because signals.py no longer exists
        pass


def ready(self):
    import users.signals
