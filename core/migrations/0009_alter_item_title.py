# Generated by Django 4.0.3 on 2022-03-15 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_item_slug_alter_item_label_alter_item_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='title',
            field=models.CharField(max_length=100),
        ),
    ]