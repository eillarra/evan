import json

from openpyxl.styles import Alignment

from evan.services.excel import ModelExcelWriter


class AbstractsSheet(ModelExcelWriter):
    def get_sheets(self) -> list[dict]:
        qs = self.queryset.select_related("user__profile").prefetch_related("event", "files", "reviews__user__profile")
        base_data = ["uuid", "email", "first_name", "last_name", "affiliation", "country"]
        event = qs.first().event

        sheets = [
            {
                "title": "Abstract submissions",
                "data": [
                    base_data
                    + [
                        "created_at",
                        "updated_at",
                        "is_accepted",
                        "title",
                        "authors",
                        "abstract",
                        "files",
                    ]
                ],
            }
        ]

        # custom fields?

        custom_fields = []

        for obj in qs:
            for k in obj.custom_data:
                if k not in custom_fields:
                    custom_fields.append(k)

        if custom_fields:
            sheets[0]["data"][0] = sheets[0]["data"][0] + custom_fields

        # reviewers?

        if event.config["abstracts"]:
            try:
                num_reviewers = event.custom_data["abstracts"]["max_reviewers"]
                for num in range(1, num_reviewers + 1):
                    sheets[0]["data"][0].append(f"review_{num}")
            except KeyError:
                num_reviewers = False

        # ----
        # DATA
        # ----

        for obj in qs:
            uuid = str(obj.uuid)
            user_base_data = [
                uuid,
                obj.user.email,
                obj.user.first_name,
                obj.user.last_name,
                obj.user.profile.affiliation,
                obj.user.profile.country.name,
            ]

            # abstract submissions

            abstract_data = [
                obj.created_at.replace(tzinfo=None),
                obj.updated_at.replace(tzinfo=None),
                obj.is_accepted,
                obj.title,
                obj.authors,
                obj.abstract,
                ",".join([f"https://evan.ugent.be/media/{f.file.path.split('/media/')[1]}" for f in obj.files.all()]),
            ]

            # custom fields

            custom_data = []

            if custom_fields:
                for f in custom_fields:
                    v = obj.custom_data[f] if f in obj.custom_data else None
                    custom_data.append(json.dumps(v) if type(v) in {dict, list} else v)

            # reviews

            reviews_data = []

            if num_reviewers:
                for review in obj.reviews.all():
                    if "ratings" in review.custom_data and review.custom_data["ratings"]:
                        ratings = list(review.custom_data["ratings"].items())
                        ratings.sort(key=lambda y: y[0])
                        ratings_txt = ", ".join([f"{r[0]} [{r[1]}]" for r in ratings])
                    else:
                        ratings_txt = ""

                    reviews_data.append(
                        f"""{review.user.profile.name}
----------------------------------------
{ratings_txt}
----------------------------------------

EVALUATION:
{review.evaluation}

COMMENTS:
{review.comments}"""
                    )

            sheets[0]["data"].append(user_base_data + abstract_data + custom_data + reviews_data)

        return sheets

    def set_custom_styles(self) -> None:
        ws = self.workbook.active
        wide_columns = ["A", "B"]

        for row in ws:
            for cell in row:
                if cell.column > 9:
                    cell.alignment = Alignment(vertical="top", wrap_text=True)
                    wide_columns.append(cell.column_letter)

        for column in wide_columns:
            ws.column_dimensions[column].width = 50
