import json
from datetime import UTC

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import IntegrityError
from django.utils.crypto import get_random_string

from evan.models.badges import Badge
from evan.models.contents import Content
from evan.models.coupons import Coupon
from evan.models.events import Event
from evan.models.registrations import Registration, RegistrationLog
from evan.models.rel.links import Link
from evan.models.rel.permissions import Permission
from evan.models.sessions import Session
from evan.models.sponsors import Sponsor
from evan.models.tracks import Track
from evan.models.users import AffiliationDomain, User
from evan.models.venues import Room, Venue


BATCH_SIZE = 500


def get_legacy_content_type_id(legacy_content_type_model: str) -> int:
    """Get the content type for the legacy model."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute(
            "SELECT id FROM django_content_type WHERE app_label = 'evan' AND model = %s", [legacy_content_type_model]
        )
        content_type = cursor.fetchone()

        if not content_type:
            raise Exception(f"Content type {legacy_content_type_model} not found.")

        return content_type[0]


def naive_to_aware(row: dict, fields: list[str]) -> dict:
    """Convert naive datetimes to aware datetimes for fields that have been updated."""
    for field in fields:
        row[field] = row[field].replace(tzinfo=UTC) if row[field] else None
    return row


def nulls_to_empty_string(row: dict, fields: list[str]) -> dict:
    """Replace legacy None values in the row with an empty string for fields that have been updated."""
    for field in fields:
        row[field] = row[field] or ""
    return row


def dictfetchall(cursor, json_fields: list[str] | None = None):
    "Return all rows from a cursor as a dict"
    if json_fields is None:
        json_fields = ["extra_data"]

    data = []
    columns = [col[0] for col in cursor.description]

    for row in cursor.fetchall():
        for field in json_fields:
            if field in columns:
                index = columns.index(field)
                row = list(row)
                row[index] = json.loads(row[index])
        data.append(dict(zip(columns, row, strict=False)))

    return data


class Command(BaseCommand):
    """Read information from existing PostgreSQL tables and migrate to new models.

    When connecting with legacy databases, sometimes raw SQL queries are needed to extract the data."""

    def handle(self, *args, **kwargs):
        """Migrate data from legacy tables to new models."""

        site = Site.objects.get(id=1)
        site.domain = "evan.ugent.be"
        site.name = "Evan"
        site.save()

        migrate_flds()
        migrate_users()
        migrate_groups()
        migrate_emails()
        migrate_socialaccounts()
        migrate_user_profiles()
        migrate_events()
        migrate_venues()
        migrate_coupons()
        migrate_tracks()
        migrate_sessions()
        migrate_registrations()
        migrate_registration_logs()
        migrate_badges()
        migrate_cms()
        migrate_sponsors()

        migrate_rel_permissions(Event, "event")

        update_created_at("evan_registration", Registration)
        update_updated_at("evan_registration", Registration)


def migrate_flds():
    """Migrate affiliation domains from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM tmp_fld")
        rows = dictfetchall(cursor)

        for row in rows:
            AffiliationDomain(**row).save()


def migrate_users():
    """Migrate users from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM auth_user")
        rows = dictfetchall(cursor)

        for row in rows:
            row = naive_to_aware(row, ["date_joined", "last_login"])
            row["email"] = row["email"].lower()
            try:
                User(**row).save()
            except IntegrityError as exc:
                if "hipeac_user.username" in str(exc):
                    row["username"] = row["username"] + get_random_string(5)
                    User(**row).save()


def migrate_user_profiles():
    """Migrate user profiles from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_profile")
        rows = dictfetchall(cursor, json_fields=["custom_data"])
        bulk = []

        for row in rows:
            row = naive_to_aware(row, ["updated_at"])
            nulls_to_empty_string(row, ["country", "affiliation"])
            user = User.objects.get(id=row["user_id"])
            user.updated_at = row["updated_at"]
            user.country = row["country"]
            user.affiliation = row["affiliation"]
            user.extra_data = row["custom_data"]
            bulk.append(user)

            if len(bulk) == BATCH_SIZE:
                User.objects.bulk_update(bulk, ["country", "updated_at", "affiliation", "extra_data"])
                bulk = []

        if bulk:
            User.objects.bulk_update(bulk, ["country", "updated_at", "affiliation", "extra_data"])


def migrate_groups():
    """Migrate groups from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM auth_group")
        rows = dictfetchall(cursor)

        for row in rows:
            DjangoGroup(**row).save()

        cursor.execute("SELECT * FROM auth_user_groups")
        rows = dictfetchall(cursor)

        for row in rows:
            group = DjangoGroup.objects.get(id=row["group_id"])
            user = User.objects.get(id=row["user_id"])
            user.groups.add(group)


def migrate_emails():
    """Migrate emails from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM account_emailaddress")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            row["email"] = row["email"].lower()
            bulk.append(EmailAddress(**row))

        EmailAddress.objects.bulk_create(bulk)


def migrate_socialaccounts():
    """Migrate social accounts from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        table_to_model = {
            "socialaccount_socialapp": SocialApp,
            "socialaccount_socialaccount": SocialAccount,
        }

        for legacy_table, Model in table_to_model.items():
            cursor.execute(f"SELECT * FROM {legacy_table}")
            rows = dictfetchall(cursor, json_fields=["extra_data", "settings"])

            for row in rows:
                if legacy_table == "socialaccount_socialaccount":
                    row = naive_to_aware(row, ["date_joined", "last_login"])
                Model(**row).save()


def migrate_events():
    """Migrate events from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_event")
        rows = dictfetchall(cursor, json_fields=["config", "custom_data", "custom_fields"])

        for row in rows:
            row = naive_to_aware(row, ["registration_early_deadline", "registration_deadline", "payments_activation"])
            row = nulls_to_empty_string(
                row, ["presentation", "website", "hashtag", "wbs_element", "ingenico_salt", "signature", "email"]
            )

            if "dates" in row["custom_data"]:
                for date in row["custom_data"]["dates"]:
                    if "end_date" in date and (date["end_date"] == "" or date["end_date"] == date["start_date"]):
                        date["end_date"] = None
                    try:
                        date.pop("key")
                    except KeyError:
                        pass

            row["extra_data"] = (
                {"important_dates": row["custom_data"]["dates"]} if "dates" in row["custom_data"] else {}
            )
            row["config"] = {}
            website = None

            if row["website"]:
                website = row["website"]

            if row["wbs_element"]:
                payments_config = {
                    "type": "ugent",
                    "wbs_element": row["wbs_element"],
                    "ingenico_salt": row["ingenico_salt"],
                    "allow_invoices": bool(row["allows_invoices"]),
                }

                if row["payments_activation"]:
                    payments_config["activation_date"] = str(row["payments_activation"].date())

                row["config"] = {"payments": payments_config}

            del (
                row["custom_data"],
                row["wbs_element"],
                row["ingenico_salt"],
                row["allows_invoices"],
                row["test_mode"],
                row["payments_activation"],
            )

            event = Event(**row)

            if website:
                Link.objects.create(content_object=event, url=website, type="website")

            event.save()


def migrate_coupons():
    """Migrate coupons from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_coupon")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            row = naive_to_aware(row, ["created_at"])
            bulk.append(Coupon(**row))

        Coupon.objects.bulk_create(bulk)


def migrate_sessions():
    """Migrate sessions from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_session")
        rows = dictfetchall(cursor, json_fields=["extra_data"])

        for row in rows:
            row = naive_to_aware(row, ["start_at", "end_at", "created_at", "updated_at"])
            row = nulls_to_empty_string(row, ["summary"])
            row["description"] = row["summary"]
            del row["summary"]
            website = None

            if row["website"]:
                website = row["website"]

            del row["website"]
            session = Session(**row)
            session.save()

            if website:
                Link.objects.create(content_object=session, url=website, type="website")


def migrate_registrations():
    """Migrate registrations from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_registration")
        rows = dictfetchall(cursor, json_fields=["custom_data"])
        bulk = []

        for row in rows:
            row = naive_to_aware(row, ["created_at", "updated_at"])
            row["extra_data"] = row["custom_data"]
            del row["custom_data"]
            bulk.append(Registration(**row))

        Registration.objects.bulk_create(bulk)


def migrate_registration_logs():
    """Migrate registration logs from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_registrationlog")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            row = naive_to_aware(row, ["created_at"])
            bulk.append(RegistrationLog(**row))

        RegistrationLog.objects.bulk_create(bulk)


def migrate_badges():
    """Migrate badges from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_badge")
        rows = dictfetchall(cursor, json_fields=["extra_data"])
        bulk = []

        for row in rows:
            row = nulls_to_empty_string(row, ["custom_color"])
            bulk.append(Badge(**row))

        Badge.objects.bulk_create(bulk)


def migrate_cms():
    """Migrate CMS content from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_content")
        rows = dictfetchall(cursor, json_fields=["config"])
        bulk = []

        for row in rows:
            row = nulls_to_empty_string(row, ["value"])
            config = {}
            if "uploader" in row["config"] and row["config"]["uploader"] is not False:
                config["file_uploader"] = row["config"]["uploader"]
            if "marked" in row["config"]:
                config["markdown"] = row["config"]["marked"]
            row["config"] = config
            content = Content(**row)
            content.clean()
            bulk.append(content)

        Content.objects.bulk_create(bulk)


def migrate_sponsors():
    """Migrate sponsors from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_sponsor")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            bulk.append(Sponsor(**row))

        Sponsor.objects.bulk_create(bulk)


def migrate_tracks():
    """Migrate tracks from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_track")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            bulk.append(Track(**row))

        Track.objects.bulk_create(bulk)


def migrate_venues():
    """Migrate venues and rooms from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT * FROM evan_venue")
        rows = dictfetchall(cursor, json_fields=["extra_data"])

        for row in rows:
            row = nulls_to_empty_string(row, ["city", "presentation"])
            website = None

            if row["website"]:
                website = row["website"]

            del row["website"], row["gmaps"]
            venue = Venue(**row)
            venue.save()

            if website:
                Link.objects.create(content_object=venue, url=website, type="website")

        cursor.execute("SELECT * FROM evan_room")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            bulk.append(Room(**row))

        Room.objects.bulk_create(bulk)


def migrate_rel_permissions(Model, legacy_content_type_model):
    """Migrate permissions from the legacy database to the new database."""

    with connections["legacy"].cursor() as cursor:
        content_type_id = get_legacy_content_type_id(legacy_content_type_model)
        cursor.execute(f"SELECT * FROM evan_permission WHERE content_type_id = {content_type_id}")
        rows = dictfetchall(cursor)

        for row in rows:
            obj = Model.objects.get(id=row["object_id"])
            Permission(content_object=obj, level=row["level"], user_id=row["user_id"]).save()


def update_created_at(legacy_table, Model):
    """Use real created_at values from the legacy database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT * FROM {legacy_table}")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            obj = Model.objects.get(id=row["id"])
            row = naive_to_aware(row, ["created_at"])
            obj.created_at = row["created_at"]
            bulk.append(obj)

            if len(bulk) == BATCH_SIZE:
                Model.objects.bulk_update(bulk, ["created_at"])
                bulk = []

        if bulk:
            Model.objects.bulk_update(bulk, ["created_at"])


def update_updated_at(legacy_table, Model):
    """Use real updated_at values from the legacy database."""

    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT * FROM {legacy_table}")
        rows = dictfetchall(cursor)
        bulk = []

        for row in rows:
            obj = Model.objects.get(id=row["id"])
            row = naive_to_aware(row, ["updated_at"])
            obj.updated_at = row["updated_at"]
            bulk.append(obj)

            if len(bulk) == BATCH_SIZE:
                Model.objects.bulk_update(bulk, ["updated_at"])
                bulk = []

        if bulk:
            Model.objects.bulk_update(bulk, ["updated_at"])
