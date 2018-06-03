# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-03 09:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20180603_2107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='tags',
            field=models.ManyToManyField(help_text='Only queries tagged with these tags will be run on this host.', to='api.Tag'),
        ),
        migrations.AlterField(
            model_name='logquery',
            name='tags',
            field=models.ManyToManyField(help_text='Only hosts tagged with these tags will run these queries. Specifying no tags makes a query run on all hosts.', to='api.Tag'),
        ),
    ]