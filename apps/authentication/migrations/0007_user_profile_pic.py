# Generated by Django 5.2.1 on 2025-06-12 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0006_alter_user_username"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="profile_pic",
            field=models.ImageField(blank=True, null=True, upload_to="profile_pics/"),
        ),
    ]
