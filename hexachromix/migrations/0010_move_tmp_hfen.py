# Generated by Django 5.0.1 on 2024-01-15 20:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('hexachromix', '0009_alter_game_id_alter_gameplayer_id_alter_move_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='move',
            name='tmp_hfen',
            field=models.CharField(editable=False, max_length=32, null=True),
        ),
    ]
