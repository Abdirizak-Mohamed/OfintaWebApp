# Generated by Django 2.0.3 on 2018-10-12 09:56

from django.db import migrations, models


def fix_duplicates(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for o in Order.objects.all():
        o.order_number = o.pk
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_auto_20181012_0951'),
    ]

    operations = [
        migrations.RunPython(fix_duplicates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.BigIntegerField(unique=True, verbose_name='order number'),
        ),
    ]