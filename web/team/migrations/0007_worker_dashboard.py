# Generated by Django 3.1.4 on 2021-01-27 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0006_auto_20200201_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='dashboard',
            field=models.URLField(default='', verbose_name='dashboard'),
        ),
    ]
