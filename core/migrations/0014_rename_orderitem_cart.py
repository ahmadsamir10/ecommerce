# Generated by Django 4.0.3 on 2022-03-16 13:06

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0013_orderitem_quantity_orderitem_user'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OrderItem',
            new_name='Cart',
        ),
    ]