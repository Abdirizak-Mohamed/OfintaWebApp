# Generated by Django 2.0.3 on 2018-10-10 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_verification_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='pending_transaction',
            field=models.BooleanField(default=False, verbose_name='pending transaction'),
        ),
    ]
