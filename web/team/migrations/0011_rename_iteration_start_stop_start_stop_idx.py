# Generated by Django 5.0.7 on 2024-08-14 17:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("team", "0010_alter_worker_options_worker_order"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="iteration",
            new_name="start_stop_idx",
            old_fields=("start", "stop"),
        ),
    ]
