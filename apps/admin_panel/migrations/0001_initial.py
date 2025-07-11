# Generated by Django 5.2.1 on 2025-05-26 20:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("trading", "0001_initial"),
        ("wallets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("approve_deposit", "Approve Deposit"),
                            ("reject_deposit", "Reject Deposit"),
                            ("approve_withdrawal", "Approve Withdrawal"),
                            ("reject_withdrawal", "Reject Withdrawal"),
                            ("adjust_trade_profit", "Adjust Trade Profit"),
                            ("approve_kyc", "Approve KYC"),
                            ("reject_kyc", "Reject KYC"),
                        ],
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "admin_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="admin_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "target_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_admin_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "trade",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="trading.trade",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="wallets.transaction",
                    ),
                ),
            ],
        ),
    ]
