import json

from typing import Dict, List

from evan.services.excel import ModelExcelWriter


class AbstractsSheet(ModelExcelWriter):
    def get_sheets(self) -> List[Dict]:
        qs = self.queryset.select_related("user__profile").prefetch_related("files")
        base_data = ["uuid", "email", "first_name", "last_name", "affiliation", "country"]

        sheets = [
            {
                "title": "Abstract submissions",
                "data": [
                    base_data
                    + [
                        "title",
                        "authors",
                        "created_at",
                        "updated_at",
                        "is_accepted",
                        "abstract",
                        "files",
                    ]
                ],
            }
        ]

        custom_fields = []

        for obj in qs:
            for k in obj.custom_data.keys():
                if k not in custom_fields:
                    custom_fields.append(k)

        if custom_fields:
            sheets[0]["data"][0] = sheets[0]["data"][0] + custom_fields

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

            # Abstract submissions

            abstract_data = [
                obj.title,
                obj.authors,
                obj.created_at.replace(tzinfo=None),
                obj.updated_at.replace(tzinfo=None),
                obj.is_accepted,
                obj.abstract,
                ",".join([f"https://evan.ugent.be/media/{f.file.path.split('/media/')[1]}" for f in obj.files.all()]),
            ]

            # Custom fields

            if custom_fields:
                custom_data = []

                for f in custom_fields:
                    v = obj.custom_data[f] if f in obj.custom_data else None
                    custom_data.append(json.dumps(v) if type(v) in {dict, list} else v)

            sheets[0]["data"].append(user_base_data + abstract_data + custom_data)

        return sheets
