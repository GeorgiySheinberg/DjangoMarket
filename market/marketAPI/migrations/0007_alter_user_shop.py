# Generated by Django 5.1.2 on 2024-10-27 17:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketAPI', '0006_user_shop_user_type_alter_user_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='shop',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user', to='marketAPI.shop'),
        ),
    ]
