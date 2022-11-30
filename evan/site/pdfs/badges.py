import os

from django.conf import settings
from django.template.defaultfilters import date as date_filter
from reportlab.graphics.shapes import Drawing, Image, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from typing import Optional

from evan.services.pdf import PdfResponse
from evan.services.pdf.styles import UGENT_BLUE, UGENT_YELLOW
from evan.services.pdf.wrapdf import Wrapdf


def get_font_size(text, *, max_size: float, char_max: int) -> float:
    """Return a text size based on the length of the text."""
    if len(text) <= char_max:
        return max_size
    return max_size / (len(text) / char_max)


def draw_badge(
    event_name: str,
    event_hashtag: str,
    event_info: str,
    attendee_name: str,
    color: HexColor,
    show_social: bool = False,
    institution: Optional[str] = None,
    country: Optional[str] = None,
) -> Drawing:
    side_margin = 6 * mm  # a minimum on the sides for the printers
    width = (210 * mm) - (2 * side_margin)
    height = 85 * mm
    logo_path = os.path.join(settings.SITE_ROOT, "static", "images", "hipeac--avatar.png")

    draw = Drawing(width, height)
    draw.add(Rect(0, 0, width, 10 * mm, fillColor=color, strokeColor=color))
    draw.add(Rect(0, 10 * mm, width, 63 * mm, fillColor="white", strokeColor="white"))
    draw.add(Rect(0, 73 * mm, width, 10 * mm, fillColor="black", strokeColor="black"))
    draw.add(Rect(0, 83 * mm, width, 2 * mm, fillColor="white", strokeColor="white"))

    for x, text in [(width * 0.25, event_name), (width * 0.75, f"#{event_hashtag}")]:
        draw.add(
            String(
                x,
                height - (8.5 * mm),
                text,
                fontName="Roboto Light",
                fillColor="white",
                fontSize=13,
                textAnchor="middle",
            )
        )

    has_logo = False

    for x in [width * 0.25, width * 0.75]:
        image_width = 15 * mm

        if not has_logo:
            draw.add(Image(x - (image_width / 2), 12 * mm, image_width, image_width, logo_path))

        draw.add(
            String(
                x,
                55 * mm,
                attendee_name,
                fontName="Roboto Medium",
                fillColor="black",
                fontSize=get_font_size(attendee_name, max_size=26.0, char_max=17),
                textAnchor="middle",
            )
        )

        if institution:
            draw.add(
                String(
                    x,
                    43 * mm,
                    institution,
                    fontName="Roboto Light",
                    fillColor="black",
                    fontSize=get_font_size(institution, max_size=14.0, char_max=36),
                    textAnchor="middle",
                )
            )

        if country:
            draw.add(
                String(
                    x,
                    37 * mm,
                    country,
                    fontName="Roboto Light",
                    fillColor="black",
                    fontSize=get_font_size(country, max_size=11.0, char_max=50),
                    textAnchor="middle",
                )
            )

        draw.add(
            String(
                x,
                3 * mm,
                event_info,
                fontName="Roboto Light",
                fillColor="white",
                fontSize=13,
                textAnchor="middle",
            )
        )

    if show_social:
        draw.add(
            String(
                width / 2,
                -6 * mm,
                "*",
                fontName="Roboto Bold",
                fillColor="white",
                fontSize=66,
                textAnchor="middle",
            )
        )

    return draw


class BadgesPdfMaker:
    def __init__(self, *, registrations, filename: str, as_attachment: bool = True):
        self._response = PdfResponse(filename=filename, as_attachment=as_attachment)
        self.registrations = (
            registrations.select_related("coupon", "event", "user__profile")
            .order_by("user__first_name", "user__last_name")
        )
        self.make_pdf()

    def make_pdf(self):
        side_margin = 6 * mm  # a minimum on the sides for the printers

        with Wrapdf(margins=[10 * mm, 0, 10 * mm, side_margin]) as pdf:
            i = 0

            for reg in self.registrations:
                i += 1
                badge_color = HexColor(UGENT_BLUE)
                event_name = reg.event.name
                event_info = (
                    f"{date_filter(reg.event.start_date, ('F j'))}-{date_filter(reg.event.end_date, ('j'))}, "
                    f"{reg.event.city}, {reg.event.country.name}"
                )

                draw = draw_badge(
                    event_name=event_name,
                    event_hashtag=reg.event.hashtag,
                    event_info=event_info,
                    attendee_name=reg.user.profile.name,
                    color=badge_color,
                    institution=reg.user.profile.affiliation,
                    country=reg.user.profile.country.name,
                    show_social=False,
                )

                pdf.parts.append(draw)

                """
                TODO: fix
                if reg.custom_data['accompanying_persons']:
                    print(reg.custom_data['accompanying_persons'])
                    for person in reg.accompanying_persons.all():
                        i += 1
                        draw = draw_badge(
                            event_name=event_name,
                            event_hashtag=reg.event.hashtag,
                            event_info=event_info,
                            attendee_name=person.name,
                            color=HexColor(UGENT_YELLOW),
                            institution=None,
                            country="-",
                            show_social=False,
                        )
                        pdf.parts.append(draw)
                """

                if i % 3 == 0:
                    pdf.add_page_break()

            self._response.write(pdf.get())

    @property
    def response(self) -> PdfResponse:
        return self._response
