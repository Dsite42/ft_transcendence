# Generated by Django 4.2.13 on 2024-06-05 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontapp', '0004_rename_datetime_game_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]