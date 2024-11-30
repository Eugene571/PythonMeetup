# Generated by Django 5.1.3 on 2024-11-30 11:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meetup', '0003_rename_users_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='speaker',
            name='telegram_id',
        ),
        migrations.AddField(
            model_name='speaker',
            name='user',
            field=models.ForeignKey(blank=True, default=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='speakers', to='Meetup.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_speaker',
            field=models.BooleanField(default=False, verbose_name='Является ли пользователь докладчиком'),
        ),
    ]
