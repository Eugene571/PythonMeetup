# Generated by Django 5.1.3 on 2024-11-30 17:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meetup', '0006_alter_user_is_speaker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='start_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 30, 17, 25, 39, 842402, tzinfo=datetime.timezone.utc), verbose_name='Дата и время начала'),
        ),
    ]
