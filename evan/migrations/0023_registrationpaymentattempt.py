from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("evan", "0022_add_fee_online_only"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistrationPaymentAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.CharField(max_length=128, unique=True)),
                ("expected_amount", models.PositiveSmallIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                            ("obsolete", "Obsolete"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("payid", models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ("callback_data", models.JSONField(blank=True, default=dict)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "registration",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="payment_attempts",
                        to="evan.registration",
                    ),
                ),
            ],
            options={
                "db_table": "evan_log_registration_payment_attempt",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="registrationpaymentattempt",
            index=models.Index(fields=["registration", "status"], name="evan_regist_registr_0c2aab_idx"),
        ),
    ]
