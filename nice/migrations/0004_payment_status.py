# Generated by Django 4.2.10 on 2024-02-23 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nice', '0003_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')], default='Pending', max_length=20),
        ),
    ]
