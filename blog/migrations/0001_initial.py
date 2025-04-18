# Generated by Django 5.0.13 on 2025-04-09 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('reply', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='StudentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100)),
                ('category', models.CharField(max_length=100)),
                ('request_type', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('attachment', models.FileField(blank=True, null=True, upload_to='requests/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
