from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("evan", "0022_auto_20200915_1039"),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE `evan`.`evan_coupon` "
            "DROP INDEX `evan_coupon_code_196326_idx`, ADD INDEX `evan_coupon_code_196326_idx` (`code`) USING HASH;"
        ),
        migrations.RunSQL(
            "ALTER TABLE `evan`.`evan_event` "
            "DROP INDEX `evan_event_code_de03e5_idx`, ADD INDEX `evan_event_code_de03e5_idx` (`code`) USING HASH;"
        ),
        migrations.RunSQL(
            "ALTER TABLE `evan`.`evan_registration` "
            "DROP INDEX `evan_regist_uuid_df76cd_idx`, ADD INDEX `evan_regist_uuid_df76cd_idx` (`uuid`) USING HASH;"
        ),
    ]
