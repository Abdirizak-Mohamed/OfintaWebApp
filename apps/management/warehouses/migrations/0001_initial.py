# Generated by Django 2.0.3 on 2018-08-01 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0001_initial'),
        ('shared', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, verbose_name='code')),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shared.Location', verbose_name='location')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouses', to='shops.Shop', verbose_name='shop')),
            ],
        ),
    ]