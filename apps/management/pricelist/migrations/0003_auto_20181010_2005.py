# Generated by Django 2.0.3 on 2018-10-10 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricelist', '0002_pricelistitem_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pricelistitem',
            name='item_id',
            field=models.CharField(max_length=255, verbose_name='item id'),
        ),
    ]
