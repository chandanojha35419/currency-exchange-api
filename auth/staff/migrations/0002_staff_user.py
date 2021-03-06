# Generated by Django 2.2.12 on 2021-09-20 10:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_admin_and_bot_user(apps, schema_editor):
    from auth.staff.models import create_staff
    from auth.staff import _get_or_create_bot

    staff = create_staff("admin@classicinformatics.com", password="cli", name="Admin")
    staff.user.username = "admin"
    staff.user.is_superuser = True
    staff.user.save()

    _get_or_create_bot()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(create_admin_and_bot_user)
    ]
