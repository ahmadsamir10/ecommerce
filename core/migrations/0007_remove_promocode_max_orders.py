# Generated by Django 4.0.3 on 2022-06-08 01:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_order_promo_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='promocode',
            name='max_orders',
        ),
    ]