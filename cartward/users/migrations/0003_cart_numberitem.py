# Generated by Django 3.1.7 on 2021-03-26 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_cart'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='numberitem',
            field=models.IntegerField(default=0),
        ),
    ]
