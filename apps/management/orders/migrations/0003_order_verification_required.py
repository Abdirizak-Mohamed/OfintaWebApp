# Generated by Django 2.0.3 on 2018-10-09 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20181009_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='verification_required',
            field=models.BooleanField(default=True, verbose_name='verification by the code is required'),
        ),
    ]
