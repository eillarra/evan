from typing import Dict, List

from evan.services.excel import ModelExcelWriter


class RegistrationsOverview(ModelExcelWriter):
    def get_sheets(self) -> List[Dict]:
        qs = self.queryset.select_related("user__profile", "coupon").prefetch_related(
            "user__profile__dietary", "days", "sessions"
        )

        sheets = [
            {
                "title": "Registrations",
                "data": [
                    [
                        "uuid",
                        "email",
                        "first_name",
                        "last_name",
                        "affiliation",
                        "country",
                        "fee_type",
                        "base_fee",
                        "extra_fees",
                        "manual_extra_fees",
                        "coupon",
                        "invoice_requested",
                        "invoice_sent",
                        "paid",
                        "paid_via_invoice",
                        "saldo",
                        "created_at",
                        "updated_at",
                    ]
                ],
            },
            {
                "title": "Visum",
                "data": [
                    [
                        "uuid",
                        "email",
                        "first_name",
                        "last_name",
                        "affiliation",
                        "country",
                        "visa_requested",
                        "visa_sent",
                    ]
                ],
            },
            {
                "title": "Dietary",
                "data": [
                    ["uuid", "email", "first_name", "last_name", "affiliation", "country", "dietary_requirements"]
                ],
            }
        ]

        for obj in qs:
            sheets[0]["data"].append(
                [
                    str(obj.uuid),
                    obj.user.email,
                    obj.user.first_name,
                    obj.user.last_name,
                    obj.user.profile.affiliation,
                    obj.user.profile.country.name,
                    obj.fee_type,
                    obj.base_fee,
                    obj.extra_fees,
                    obj.manual_extra_fees,
                    str(obj.coupon),
                    obj.invoice_requested,
                    obj.invoice_sent,
                    obj.paid,
                    obj.paid_via_invoice,
                    obj.saldo,
                    obj.created_at,
                    obj.updated_at,
                ]
            )
            sheets[1]["data"].append(
                [
                    str(obj.uuid),
                    obj.user.email,
                    obj.user.first_name,
                    obj.user.last_name,
                    obj.user.profile.affiliation,
                    obj.user.profile.country.name,
                    obj.visa_requested,
                    obj.visa_sent,
                ]
            )
            sheets[2]["data"].append(
                [
                    str(obj.uuid),
                    obj.user.email,
                    obj.user.first_name,
                    obj.user.last_name,
                    obj.user.profile.affiliation,
                    obj.user.profile.country.name,
                    str(obj.user.profile.dietary),
                ]
            )

        return sheets
