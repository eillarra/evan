import importlib
import os
from typing import TYPE_CHECKING

from django.conf import settings
from django.template.defaultfilters import date as date_filter
from reportlab.graphics.shapes import Drawing, Image, Rect, String  # type: ignore
from reportlab.lib.colors import Color, HexColor, black, white  # type: ignore
from reportlab.lib.units import mm  # type: ignore
from svglib.svglib import svg2rlg  # type: ignore

from evan.services.pdf import PdfResponse
from evan.services.pdf.styles import UGENT_BLUE
from evan.services.pdf.wrapdf import Wrapdf


if TYPE_CHECKING:
    from evan.models.registrations import Registration


def get_font_size(text, *, max_size: float, char_max: int) -> float:
    """Return a text size based on the length of the text."""
    if len(text) <= char_max:
        return max_size
    return max_size / (len(text) / char_max)


def get_custom_icons(event_code: str, registration: Registration, person_data: dict | None = None) -> list[dict]:
    """Get custom icons for a registration based on event code.

    :param event_code: The event code to check for custom extensions.
    :param registration: The registration to get custom info for.
    :param person_data: Optional data for accompanying person.
    :returns: List of icon dictionaries with 'filename' and optional styling info.
    """
    try:
        module_name = f"evan.site.pdfs.custom.{event_code}"
        custom_module = importlib.import_module(module_name)
        if hasattr(custom_module, "get_custom_info"):
            return custom_module.get_custom_info(registration, person_data)
    except ImportError:
        # No custom module for this event
        pass
    return []


def draw_badge(  # type: ignore
    event_name: str,
    event_hashtag: str,
    event_info: str,
    attendee_name: str,
    color: Color,
    show_social: bool = False,
    institution: str | None = None,
    country: str | None = None,
    custom_icons: list[dict] | None = None,
) -> Drawing:
    side_margin = 6 * mm  # a minimum on the sides for the printers
    width = (210 * mm) - (2 * side_margin)
    height = 85 * mm
    logo_path = os.path.join(settings.SITE_ROOT, "static", "images", "hipeac--avatar.png")

    draw = Drawing(width, height)
    draw.add(Rect(0, 0, width, 10 * mm, fillColor=color, strokeColor=color))  # type: ignore
    draw.add(Rect(0, 10 * mm, width, 63 * mm, fillColor=white, strokeColor=white))  # type: ignore
    draw.add(Rect(0, 73 * mm, width, 10 * mm, fillColor=color, strokeColor=color))  # type: ignore
    draw.add(Rect(0, 83 * mm, width, 2 * mm, fillColor=white, strokeColor=white))  # type: ignore

    for x, text in [(width * 0.25, event_name), (width * 0.75, f"#{event_hashtag}")]:
        draw.add(
            String(
                x,
                height - (8.5 * mm),
                text,
                fontName="Roboto Light",
                fillColor=white,
                fontSize=13,
                textAnchor="middle",
            )
        )

    has_logo = False

    for x in [width * 0.25, width * 0.75]:
        image_width = 30 * mm
        image_height = (94 / 359) * image_width

        if not has_logo:
            draw.add(Image(x - (image_width / 2), image_height + (8 * mm), image_width, image_height, logo_path))

        draw.add(
            String(
                x,
                55 * mm,
                attendee_name,
                fontName="Roboto Medium",
                fillColor=black,
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
                    fillColor=black,
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
                    fillColor=black,
                    fontSize=get_font_size(country, max_size=11.0, char_max=50),
                    textAnchor="middle",
                )
            )

        # Draw custom icons if available
        if custom_icons:
            icon_size = 7 * mm  # Size for each icon
            icon_spacing = 2 * mm  # Horizontal spacing between icons
            # Position icons closer to the lower band
            icon_y = 13 * mm

            # Separate social icons from camera icon
            social_icons = [icon for icon in custom_icons if not icon["filename"].startswith("camera")]
            camera_icons = [icon for icon in custom_icons if icon["filename"].startswith("camera")]

            # Draw social icons on the left side
            if social_icons:
                # Start from left margin
                start_x = x - (width * 0.20)  # Position on left side of badge half

                for i, icon_info in enumerate(social_icons):
                    icon_path = os.path.join(settings.SITE_ROOT, "static", "images", "icons", icon_info["filename"])
                    if os.path.exists(icon_path):
                        icon_x = start_x + i * (icon_size + icon_spacing)
                        try:
                            # Convert SVG to ReportLab drawing
                            svg_drawing = svg2rlg(icon_path)
                            if svg_drawing is not None:
                                # Scale the SVG to fit our icon size
                                scale_x = icon_size / svg_drawing.width
                                scale_y = icon_size / svg_drawing.height
                                scale = min(scale_x, scale_y)  # Maintain aspect ratio

                                svg_drawing.width = svg_drawing.width * scale
                                svg_drawing.height = svg_drawing.height * scale
                                svg_drawing.scale(scale, scale)

                                # Position the SVG
                                svg_drawing.shift(icon_x, icon_y)
                                draw.add(svg_drawing)
                        except Exception:
                            # Fallback: try to use as regular image (for PNG/JPG)
                            try:
                                draw.add(Image(icon_x, icon_y, icon_size, icon_size, icon_path))
                            except Exception:
                                # Skip this icon if it can't be loaded
                                pass

            # Draw camera icon on the right side
            if camera_icons:
                # Position on right side of badge half
                camera_x = x + (width * 0.15)  # Position on right side of badge half

                for icon_info in camera_icons:
                    icon_path = os.path.join(settings.SITE_ROOT, "static", "images", "icons", icon_info["filename"])
                    if os.path.exists(icon_path):
                        try:
                            # Convert SVG to ReportLab drawing
                            svg_drawing = svg2rlg(icon_path)
                            if svg_drawing is not None:
                                # Scale the SVG to fit our icon size
                                scale_x = icon_size / svg_drawing.width
                                scale_y = icon_size / svg_drawing.height
                                scale = min(scale_x, scale_y)  # Maintain aspect ratio

                                svg_drawing.width = svg_drawing.width * scale
                                svg_drawing.height = svg_drawing.height * scale
                                svg_drawing.scale(scale, scale)

                                # Position the SVG
                                svg_drawing.shift(camera_x, icon_y)
                                draw.add(svg_drawing)
                        except Exception:
                            # Fallback: try to use as regular image (for PNG/JPG)
                            try:
                                draw.add(Image(camera_x, icon_y, icon_size, icon_size, icon_path))
                            except Exception:
                                # Skip this icon if it can't be loaded
                                pass

        draw.add(
            String(
                x,
                3 * mm,
                event_info,
                fontName="Roboto Light",
                fillColor=white,
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
                fillColor=white,
                fontSize=66,
                textAnchor="middle",
            )
        )

    return draw


class BadgesPdfMaker:
    def __init__(self, *, registrations, filename: str, as_attachment: bool = True):
        self._response = PdfResponse(filename=filename, as_attachment=as_attachment)
        self.registrations = registrations.select_related("coupon", "event", "user")
        self.make_pdf()

    def _sort_registrations(self, registrations, sort_by: str):
        """Sort registrations based on the sort_by field."""
        if sort_by == "last_name":
            return registrations.order_by("user__last_name", "user__first_name")
        else:
            return registrations.order_by("user__first_name", "user__last_name")

    def _group_registrations(self, registrations, group_by: str):
        """Group registrations based on the group_by field."""
        if group_by == "fee":
            groups = {}
            for reg in registrations:
                fee_type = reg.fee_type or "no_fee"
                if fee_type not in groups:
                    groups[fee_type] = []
                groups[fee_type].append(reg)
            return [groups[key] for key in sorted(groups.keys())]
        elif group_by == "color":
            event = registrations.first().event if registrations else None
            if not event:
                return [list(registrations)]

            badge_config = event.badges_configuration
            fee_colors = badge_config.get("fee_colors", {})
            default_color = badge_config.get("default", "#2196F3")

            color_groups = {}
            for reg in registrations:
                color = fee_colors[reg.fee_type] if reg.fee_type and reg.fee_type in fee_colors else default_color

                if color not in color_groups:
                    color_groups[color] = []
                color_groups[color].append(reg)

            return [color_groups[color] for color in sorted(color_groups.keys())]
        else:
            return [list(registrations)]

    def make_pdf(self):
        side_margin = 6 * mm

        with Wrapdf(margins=[10 * mm, 0, 10 * mm, side_margin]) as pdf:
            event = self.registrations.first().event
            badge_config = event.badges_configuration

            sort_by = badge_config.get("sort_by", "first_name")
            group_by = badge_config.get("group_by", "none")

            sorted_registrations = self._sort_registrations(self.registrations, sort_by)

            registration_groups = self._group_registrations(sorted_registrations, group_by)

            badge_count = 0

            for group in registration_groups:
                for reg in group:
                    badge_count += 1
                    fee_colors = badge_config.get("fee_colors", {})
                    if reg.fee_type in fee_colors:
                        badge_color = HexColor(fee_colors[reg.fee_type])
                    else:
                        badge_color = HexColor(badge_config.get("default", UGENT_BLUE))

                    event_info = (
                        f"{date_filter(reg.event.start_date, ('F j'))}-{date_filter(reg.event.end_date, ('j'))}, "
                        f"{reg.event.city}, {reg.event.country.name}"
                    )

                    # Get custom icons for this registration
                    custom_icons = get_custom_icons(event.code, reg)

                    draw = draw_badge(
                        event_name=event.name,
                        event_hashtag=event.hashtag,
                        event_info=event_info,
                        attendee_name=reg.user.name,
                        color=badge_color,
                        institution=reg.user.affiliation,
                        country=reg.user.country.name,
                        show_social=False,
                        custom_icons=custom_icons,
                    )

                    pdf.parts.append(draw)

                    if badge_count % 3 == 0:
                        pdf.add_page_break()

                    accompanying_persons = reg.extra_data.get("accompanying_persons", [])
                    for person in accompanying_persons:
                        badge_count += 1
                        guest_color = HexColor(badge_config.get("guest", "#4CAF50"))

                        guest_relationship = f"guest of {reg.user.name}"

                        # Get custom icons for accompanying persons using their specific social event selections
                        custom_icons = get_custom_icons(event.code, reg, person)

                        draw = draw_badge(
                            event_name=event.name,
                            event_hashtag=event.hashtag,
                            event_info=event_info,
                            attendee_name=person["name"],
                            color=guest_color,
                            institution=None,
                            country=guest_relationship,
                            show_social=False,
                            custom_icons=custom_icons,
                        )

                        pdf.parts.append(draw)

                        if badge_count % 3 == 0:
                            pdf.add_page_break()

            self._response.write(pdf.get())

    @property
    def response(self) -> PdfResponse:
        return self._response
