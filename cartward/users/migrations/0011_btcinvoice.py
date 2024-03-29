# Generated by Django 3.1.7 on 2021-05-17 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20210420_0045'),
    ]

    operations = [
        migrations.CreateModel(
            name='Btcinvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(-1, 'Not Started'), (0, 'Unconfirmed'), (1, 'Partially Confirmed'), (2, 'Confirmed')], default=-1)),
                ('address', models.CharField(blank=True, max_length=250, null=True)),
                ('received', models.IntegerField(blank=True, null=True)),
                ('txid', models.CharField(blank=True, max_length=250, null=True)),
                ('rbf', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateField(auto_now=True)),
            ],
        ),
    ]
