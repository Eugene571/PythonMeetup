# Generated by Django 5.1.3 on 2024-11-30 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meetup', '0004_remove_speaker_telegram_id_speaker_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='telegram_id',
            field=models.BigIntegerField(blank=True, db_index=True, unique=True, verbose_name='телеграм id'),
        ),
    ]