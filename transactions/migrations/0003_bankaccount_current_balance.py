# Generated by Django 5.1 on 2024-10-15 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_alter_transaction_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='current_balance',
            field=models.IntegerField(default=0),
        ),
    ]
