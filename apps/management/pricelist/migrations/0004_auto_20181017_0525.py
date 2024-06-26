# Generated by Django 2.0.3 on 2018-10-17 05:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pricelist', '0003_auto_20181010_2005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pricelistitem',
            name='image',
            field=models.ImageField(blank=True, max_length=254, null=True, upload_to='pricelist'),
        ),
        migrations.AlterField(
            model_name='pricelistitem',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricelist_items', to='shops.Shop', verbose_name='shop'),
        ),
    ]
