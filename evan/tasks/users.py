from celery.decorators import task
from django.db import connection
from tld import get_tld

from evan.models import Profile


@task()
def update_affiliation(user_id: int) -> tuple:
    profile = Profile.objects.select_related("user").get(user_id=user_id)
    domain = get_tld(profile.user.email.split("@")[-1], as_object=True, fix_protocol=True)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tmp_fld WHERE fld = %s", [domain.fld])
        row = cursor.fetchone()

    if row:
        profile.affiliation = profile.affiliation if profile.affiliation else row[1]
        profile.country = profile.country if profile.country else row[2]
        profile.save(update_fields=["affiliation", "country"])

    return domain.fld, True if row else False, profile
