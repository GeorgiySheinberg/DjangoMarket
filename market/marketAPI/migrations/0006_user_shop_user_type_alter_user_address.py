# Generated by Django 5.1.2 on 2024-10-25 14:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketAPI', '0005_user_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='shop',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='marketAPI.shop'),
        ),
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='marketAPI.usertype'),
        ),
        migrations.AlterField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
