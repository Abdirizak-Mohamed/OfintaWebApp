# Generated by Django 2.0.3 on 2018-10-08 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0002_shop_allow_mpesa_prepayment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='allow_mpesa_prepayment',
        ),
        migrations.AddField(
            model_name='shop',
            name='allow_prepayment',
            field=models.BooleanField(default=False, verbose_name='allow prepayment'),
        ),
    ]
