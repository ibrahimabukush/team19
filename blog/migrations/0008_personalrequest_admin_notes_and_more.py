# Generated by Django 4.2.23 on 2025-06-22 23:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0007_personalrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalrequest',
            name='admin_notes',
            field=models.TextField(blank=True, help_text='הערות פנימיות למנהל בלבד', verbose_name='הערות מנהל'),
        ),
        migrations.AddField(
            model_name='personalrequest',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='תאריך טיפול'),
        ),
        migrations.AddField(
            model_name='personalrequest',
            name='processed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_personal_requests', to=settings.AUTH_USER_MODEL, verbose_name='מטופל על ידי'),
        ),
        migrations.AddField(
            model_name='personalrequest',
            name='selected_lecturer',
            field=models.ForeignKey(blank=True, help_text='המרצה הנבחר למכתב המלצה (רלוונטי רק לבקשות מכתבי המלצה)', limit_choices_to={'is_lecturer': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recommendation_requests', to=settings.AUTH_USER_MODEL, verbose_name='מרצה נבחר'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='personal_requests/', verbose_name='קובץ מצורף'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='תאריך יצירה'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='request_text',
            field=models.TextField(help_text='פירוט הבקשה', verbose_name='תוכן הבקשה'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='request_type',
            field=models.CharField(choices=[('recommendation_letter', 'בקשה למכתבי המלצה'), ('scholarships_financial_aid', 'בקשות מלגות וסיוע כלכלי'), ('academic_status_change', 'בקשת שינוי סטטוס אקדמי'), ('general_manager_inquiry', 'פניה כללית למנהל')], max_length=50, verbose_name='סוג בקשה'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'ממתין לטיפול'), ('in_progress', 'בטיפול'), ('approved', 'אושר'), ('rejected', 'נדחה')], default='pending', max_length=20, verbose_name='סטטוס'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personal_requests', to=settings.AUTH_USER_MODEL, verbose_name='סטודנט'),
        ),
        migrations.AlterField(
            model_name='personalrequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='תאריך עדכון אחרון'),
        ),
    ]
