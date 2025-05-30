# Generated by Django 5.2.1 on 2025-05-26 12:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0004_client_timezone_alter_client_age_alter_client_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 5, 26, 12, 3, 41, 753015, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='timezone',
            field=models.CharField(default='Europe/Minsk', max_length=100),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='code',
            field=models.CharField(max_length=8, unique=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
