# Generated by Django 4.0.3 on 2022-03-16 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_rename_orderitem_cart'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='title',
            new_name='item',
        ),
    ]
