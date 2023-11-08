from django.db import connection
from huey.contrib.djhuey import db_task
from tld import get_tld

from evan.models.users import User


@db_task()
def update_affiliation(user_id: int) -> tuple:
    user = User.objects.get(id=user_id)
    domain = get_tld(user.email.split("@")[-1], as_object=True, fix_protocol=True)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tmp_fld WHERE fld = %s", [domain.fld])
        row = cursor.fetchone()

    if row:
        user.affiliation = user.affiliation if user.affiliation else row[1]
        user.country = user.country if user.country else row[2]
        user.save(update_fields=["affiliation", "country"])

    return domain.fld, bool(row), user
