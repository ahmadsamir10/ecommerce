# Generated by Django 4.0.3 on 2022-03-30 04:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_payment_order_payment_info'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='amount',
            new_name='dollars',
        ),
    ]