# Generated by Django 5.0.13 on 2025-06-10 10:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_department_user_is_secretary_user_year_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_approved',
        ),
    ]
