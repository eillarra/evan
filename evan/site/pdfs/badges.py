"""Badge PDF generation using ReportLab.

Each badge is drawn twice per page row (left/right half) so printed A4 sheets
can be cut into individual cards. Behaviour (colors, icons, QR contact card)
is configured per event through :class:`~evan.models.documents.badges.BadgesConfig`.
"""

import copy
import os
import tempfile
from datetime import date  # noqa: TC003
from typing import TYPE_CHECKING

from django.conf import settings
from django.template.defaultfilters import date as date_filter
from reportlab.graphics.barcode.qr import QrCodeWidget  # type: ignore
from reportlab.graphics.shapes import Drawing, Rect, String  # type: ignore
from reportlab.lib.colors import Color, HexColor, black, white  # type: ignore
from reportlab.lib.units import mm  # type: ignore
from svglib.svglib import svg2rlg  # type: ignore

from evan.models.documents.badges import AVAILABLE_BADGE_ICONS, ICON_FILES
from evan.services.pdf import PdfResponse
from evan.services.pdf.styles import UGENT_BLUE
from evan.services.pdf.wrapdf import Wrapdf


if TYPE_CHECKING:
    from evan.models.registrations import Registration


# Layout constants (A4 sheet, cut into 85 mm high badge halves).
SIDE_MARGIN = 6 * mm  # minimum margin on sides for printers
BADGE_WIDTH = (210 * mm) - (2 * SIDE_MARGIN)
BADGE_HEIGHT = 85 * mm

# Icons row (above the bottom color band).
ICONS_DIR = os.path.join(settings.SITE_ROOT, "static", "images", "icons")
ICON_SIZE = 7 * mm
ICON_SPACING = 2 * mm
ICONS_Y = 13 * mm
ICONS_LEFT_OFFSET = 0.20  # fraction of badge width left of each half centre
ICONS_RIGHT_OFFSET = 0.15  # fraction of badge width right of each half centre

# QR contact card.
QR_SIZE = 15 * mm
QR_LEVEL = "M"

# Event logo: fitted inside this box, bottom aligned with the icon row so it
# sits between the country line and the footer color band.
LOGO_MAX_WIDTH = 30 * mm
LOGO_MAX_HEIGHT = 13 * mm
LOGO_Y = 13 * mm


def get_font_size(text: str, *, max_size: float, char_max: int) -> float:
    """Return a font size based on the length of the text.

    :param text: The text that will be rendered.
    :param max_size: Font size to use when the text fits.
    :param char_max: Number of characters that fit at ``max_size``.
    :returns: The font size to render the text with.
    """
    if len(text) < char_max:
        return max_size
    return max_size / (len(text) / char_max)


def format_event_info(*, start_date: date, end_date: date, city: str, country: str) -> str:
    """Format the event info line shown on the bottom color band of a badge.

    Year is omitted: same-month ranges collapse to ``Month D1-D2`` (e.g.
    ``August 11-14, Ghent, Belgium``); anything else falls back to full
    dates without the year.

    :param start_date: First day of the event.
    :param end_date: Last day of the event.
    :param city: City the event takes place in.
    :param country: Country the event takes place in.
    :returns: The formatted info line.
    """
    start_month = date_filter(start_date, "F")
    if start_date == end_date:
        date_part = f"{start_month} {start_date.day}"
    elif (start_date.year, start_date.month) == (end_date.year, end_date.month):
        date_part = f"{start_month} {start_date.day}-{end_date.day}"
    else:
        date_part = f"{date_filter(start_date, 'F j')} - {date_filter(end_date, 'F j')}"
    return f"{date_part}, {city}, {country}"


def build_mecard(*, name: str, affiliation: str = "", email: str = "") -> str:
    """Build a MECARD payload for a QR contact card.

    Only the fields that are set are included. Special MECARD characters
    backslash, semicolon, comma and colon are escaped.

    :param name: Full name of the contact.
    :param affiliation: Organisation or affiliation of the contact.
    :param email: Email address of the contact.
    :returns: A MECARD string ready to be encoded in a QR code.
    """

    def _escape(value: str) -> str:
        for char in ("\\", ";", ",", ":"):
            value = value.replace(char, f"\\{char}")
        return value

    fields = []
    if name:
        fields.append(f"N:{_escape(name)}")
    if affiliation:
        fields.append(f"ORG:{_escape(affiliation)}")
    if email:
        fields.append(f"EMAIL:{_escape(email)}")
    return f"MECARD:{''.join(field + ';' for field in fields)};"


def registration_allows_photos(registration: Registration) -> bool:
    """Check the attendee's photo consent for the struck camera icon.

    Consented attendees (and attendees without a recorded preference) get the
    plain camera icon; attendees who opted out get the pre-struck one.

    :param registration: The registration to check.
    :returns: False only when the attendee explicitly opted out of photography.
    """
    internal = (registration.extra_data or {}).get("_internal") or {}
    return internal.get("allow_photo_sharing", True)


def get_badge_icons(registration: Registration, person_data: dict | None = None) -> list[str]:
    """Return the ordered badge icon keys for a registration or attendee person.

    Icons are configured per social event session in ``session.extra_data``
    (``badge_icon`` key, validated against ``AVAILABLE_BADGE_ICONS``) and
    drawn in the event's agenda order.

    :param registration: The registration to get badge icons for.
    :param person_data: Optional data of an accompanying person
        (contains a ``selected_social_events`` list).
    :returns: Ordered list of icon keys without duplicates.
    """
    if person_data is not None:
        session_ids = person_data.get("selected_social_events", [])
        sessions = registration.event.sessions.filter(is_social_event=True, id__in=session_ids)
    else:
        sessions = registration.sessions.filter(is_social_event=True)

    icons: list[str] = []
    for session in sessions:
        icon = (session.extra_data or {}).get("badge_icon")
        if icon in AVAILABLE_BADGE_ICONS and icon not in icons:
            icons.append(icon)
    return icons


def build_qr_data(registration: Registration) -> str | None:
    """Build the MECARD payload for a main registration.

    :param registration: The registration to build the contact card for.
    :returns: The MECARD string, or None if no contact data is available.
    """
    return build_mecard(
        name=registration.user.name,
        affiliation=registration.user.affiliation,
        email=registration.user.email,
    )


def get_event_logo_drawing(event) -> Drawing | None:
    """Load the event's SVG logo as a reportlab drawing.

    The logo file (tagged ``logo`` on the event) may live on remote storage,
    so its bytes are copied to a temporary file before parsing.

    :param event: The event to load the logo for.
    :returns: A reportlab drawing, or None when no logo is available.
    """
    logo_file = event.get_logo_file()
    if not logo_file:
        return None
    try:
        logo_file.file.open()
        content = logo_file.file.read()
        logo_file.file.close()
    except OSError:
        return None
    if not content:
        return None
    with tempfile.NamedTemporaryFile(suffix=".svg") as temp:
        temp.write(content)
        temp.flush()
        try:
            return svg2rlg(temp.name)
        except Exception:
            return None


def draw_logo(draw: Drawing, logo_drawing: Drawing, x: float) -> None:
    """Scale the event logo to the logo box and centre it on a badge half.

    Logos vary in aspect ratio, so they are scaled to fit inside the box and
    centred on the same anchor point.

    :param draw: The reportlab drawing to add the logo to.
    :param logo_drawing: Parsed SVG logo drawing (intrinsic w/h preserved).
    :param x: Horizontal centre of the badge half in points.
    """
    width, height = logo_drawing.width, logo_drawing.height
    if not width or not height:
        return
    scale = min(LOGO_MAX_WIDTH / width, LOGO_MAX_HEIGHT / height)
    logo = copy.deepcopy(logo_drawing)
    logo.width = width * scale
    logo.height = height * scale
    logo.scale(scale, scale)
    logo.shift(x - logo.width / 2, LOGO_Y)
    draw.add(logo)


def draw_icon(draw: Drawing, icon_key: str, x: float, y: float) -> None:
    """Insert an SVG icon from the badge icon set into a drawing.

    ``icon_key`` is resolved through ``ICON_FILES`` to the original Google
    Material Symbols file name. Missing or invalid icon files are silently
    skipped; the whitelist in ``AVAILABLE_BADGE_ICONS`` is the source of truth.

    :param draw: The reportlab drawing to add the icon to.
    :param icon_key: A key from ``AVAILABLE_BADGE_ICONS`` (or ``camera_struck``).
    :param x: Horizontal position in points.
    :param y: Vertical position in points.
    """
    icon_file = ICON_FILES.get(icon_key, icon_key)
    icon_path = os.path.join(ICONS_DIR, f"{icon_file}.svg")
    if not os.path.exists(icon_path):
        return
    try:
        svg_drawing = svg2rlg(icon_path)
    except Exception:
        return
    if svg_drawing is None:
        return
    scale = min(ICON_SIZE / svg_drawing.width, ICON_SIZE / svg_drawing.height)
    svg_drawing.width = svg_drawing.width * scale
    svg_drawing.height = svg_drawing.height * scale
    svg_drawing.scale(scale, scale)
    svg_drawing.shift(x, y)
    draw.add(svg_drawing)


def draw_qr_card(draw: Drawing, qr_data: str, x: float, y: float, size: float = QR_SIZE) -> None:
    """Insert a QR code with a quiet zone into a drawing, scaled to ``size``.

    :param draw: The reportlab drawing to add the QR code to.
    :param qr_data: The string to encode (e.g. a MECARD payload).
    :param x: Horizontal position of the bottom-left corner in points.
    :param y: Vertical position of the bottom-left corner in points.
    :param size: Desired size of the QR code (including its quiet zone).
    """
    try:
        widget = QrCodeWidget(qr_data, barLevel=QR_LEVEL)
        bounds = widget.getBounds()
        qr_width, qr_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        container = Drawing(qr_width, qr_height, transform=[1, 0, 0, 1, -bounds[0], -bounds[1]])
        container.add(widget)
        scale = size / max(qr_width, qr_height)
        container.width = container.width * scale
        container.height = container.height * scale
        container.scale(scale, scale)
        container.shift(x, y)
        draw.add(container)
    except Exception:
        return


def draw_badge(  # type: ignore[misc]
    *,
    event_name: str,
    event_hashtag: str,
    event_info: str,
    attendee_name: str,
    color: Color,
    logo: Drawing | None = None,
    icons: list[str] | None = None,
    show_camera_icon: bool = False,
    no_photos: bool = False,
    qr_data: str | None = None,
    institution: str | None = None,
    country: str | None = None,
) -> Drawing:
    """Draw one badge row: two identical badge halves on one A4 width.

    :param event_name: Name of the event.
    :param event_hashtag: Social media hashtag of the event.
    :param event_info: Extra info line shown on the bottom color band.
    :param attendee_name: Name of the attendee.
    :param color: Background color for the top and bottom bands.
    :param logo: Parsed event logo drawing, or None for no logo.
        Drawn on the first (left) half only, below the attendee name.
    :param icons: Icon keys (social event icons) to draw on the right half.
    :param show_camera_icon: Whether to draw a camera icon for photo permission.
    :param no_photos: Whether the attendee opted out of photography
        (draws a pre-struck camera icon instead of the plain one).
    :param qr_data: Optional MECARD payload for the contact QR code.
    :param institution: Institution line shown under the attendee name.
    :param country: Country (or guest relationship) line.
    :returns: The reportlab drawing for the badge row.
    """
    width, height = BADGE_WIDTH, BADGE_HEIGHT
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

    for i, x in enumerate([width * 0.25, width * 0.75]):
        # Logo only on the first (left) half; the right half carries the
        # social event icons and QR contact card.
        if logo and i == 0:
            draw_logo(draw, logo, x)

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

        if qr_data and i == 1:
            # Right half: QR contact card below the name.
            draw_qr_card(draw, qr_data, x - (QR_SIZE / 2), 34 * mm, QR_SIZE)
        else:
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

        # Social event icons live on the right half ("B" side, where the QR
        # contact card can appear). The camera icon shows on both halves.
        if icons and i == 1:
            start_x = x - (width * ICONS_LEFT_OFFSET)
            for j, icon_key in enumerate(icons):
                draw_icon(draw, icon_key, start_x + j * (ICON_SIZE + ICON_SPACING), ICONS_Y)

        if show_camera_icon:
            camera_icon = "camera_struck" if no_photos else "camera"
            draw_icon(draw, camera_icon, x + (width * ICONS_RIGHT_OFFSET), ICONS_Y)

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

    return draw


class BadgesPdfMaker:
    """Builds badges PDF documents for selected event registrations."""

    def __init__(self, *, registrations, filename: str, as_attachment: bool = True):
        """Initialize the maker and generate the PDF document.

        :param registrations: Queryset or list of registrations to generate badges for.
        :param filename: Download filename for the resulting PDF.
        :param as_attachment: Whether the PDF is served as an attachment.
        """
        self._response = PdfResponse(filename=filename, as_attachment=as_attachment)
        self.registrations = registrations.select_related("coupon", "event", "user")
        self.make_pdf()

    def _sort_registrations(self, registrations, sort_by: str):
        """Sort registrations based on the sort_by field.

        :param registrations: Registrations to sort.
        :param sort_by: ``last_name`` or ``first_name`` ordering.
        :returns: Ordered registrations.
        """
        if sort_by == "last_name":
            return registrations.order_by("user__last_name", "user__first_name")
        return registrations.order_by("user__first_name", "user__last_name")

    def _group_registrations(self, registrations, group_by: str):
        """Group registrations based on the group_by field.

        :param registrations: Registrations to group.
        :param group_by: ``fee``, ``color`` or anything else for no grouping.
        :returns: List of registration groups to draw in order.
        """
        if group_by == "fee":
            groups: dict = {}
            for reg in registrations:
                fee_type = reg.fee_type or "no_fee"
                if fee_type not in groups:
                    groups[fee_type] = []
                groups[fee_type].append(reg)
            return [groups[key] for key in sorted(groups.keys())]
        if group_by == "color":
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
        return [list(registrations)]

    def make_pdf(self) -> None:
        """Build the badges PDF document for all selected registrations."""
        pdf = Wrapdf(margins=[10 * mm, 0, 10 * mm, 0])
        event = self.registrations.first().event
        badge_config = event.badges_configuration

        sort_by = badge_config.get("sort_by", "first_name")
        group_by = badge_config.get("group_by", "none")
        logo = get_event_logo_drawing(event) if badge_config.get("show_logo") else None
        icons_enabled = badge_config.get("icons_enabled", False)
        show_camera_icon = badge_config.get("show_camera_icon", False)
        qr_enabled = badge_config.get("qr_contact_card", False)

        sorted_registrations = self._sort_registrations(self.registrations, sort_by)
        registration_groups = self._group_registrations(sorted_registrations, group_by)

        badge_count = 0
        for registration_group in registration_groups:
            for reg in registration_group:
                badge_count += 1
                fee_colors = badge_config.get("fee_colors", {})
                color = (
                    HexColor(fee_colors[reg.fee_type])
                    if reg.fee_type in fee_colors
                    else HexColor(badge_config.get("default", UGENT_BLUE))
                )

                event_info = format_event_info(
                    start_date=reg.event.start_date,
                    end_date=reg.event.end_date,
                    city=reg.event.city,
                    country=reg.event.country.name,
                )

                icons = get_badge_icons(reg) if icons_enabled else []
                qr_data = build_qr_data(reg) if qr_enabled else None
                no_photos = not registration_allows_photos(reg) if show_camera_icon else False

                draw = draw_badge(
                    event_name=event.name,
                    event_hashtag=event.hashtag,
                    event_info=event_info,
                    attendee_name=reg.user.name,
                    color=color,
                    logo=logo,
                    icons=icons,
                    show_camera_icon=show_camera_icon,
                    no_photos=no_photos,
                    qr_data=qr_data,
                    institution=reg.user.affiliation,
                    country=reg.user.country.name,
                )
                draw.hAlign = "CENTER"
                pdf.parts.append(draw)
                if badge_count % 3 == 0:
                    pdf.add_page_break()

                accompanying_persons = reg.extra_data.get("accompanying_persons", [])
                for person in accompanying_persons:
                    badge_count += 1
                    guest_color = HexColor(badge_config.get("guest", "#4CAF50"))

                    guest_relationship = f"guest of {reg.user.name}"

                    person_icons = get_badge_icons(reg, person) if icons_enabled else []

                    draw = draw_badge(
                        event_name=event.name,
                        event_hashtag=event.hashtag,
                        event_info=event_info,
                        attendee_name=person["name"],
                        color=guest_color,
                        logo=logo,
                        icons=person_icons,
                        show_camera_icon=show_camera_icon,
                        no_photos=False,
                        qr_data=None,
                        institution=None,
                        country=guest_relationship,
                    )
                    draw.hAlign = "CENTER"
                    pdf.parts.append(draw)
                    if badge_count % 3 == 0:
                        pdf.add_page_break()

        self._response.write(pdf.get())

    @property
    def response(self) -> PdfResponse:
        """Return the response containing the generated PDF document.

        :returns: The PDF response.
        """
        return self._response
