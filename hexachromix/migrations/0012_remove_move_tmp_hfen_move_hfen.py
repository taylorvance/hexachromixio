# Generated by Django 5.0.1 on 2024-01-15 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hexachromix', '0011_auto_20240115_2034'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='move',
            name='tmp_hfen',
        ),
        migrations.AddField(
            model_name='move',
            name='hfen',
            field=models.CharField(default='', editable=False, max_length=32),
        ),
    ]