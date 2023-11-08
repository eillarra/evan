from pathlib import Path

from pdfino import Font, Margins, Style, Template
from reportlab.lib.pagesizes import mm


FONTS_PATH = Path(__file__).parent / "static" / "fonts"
BASE_FONT_SIZE = 9
TEXT_COLOR = "#15141A"
TEXT_LIGHT_COLOR = "#666666"
evan_BLUE = "#005eb8"
SIDE_MARGIN = 20 * mm

REPORTLAB_INNER_FRAME_PADDING = 6


class DiscoverUsTemplate(Template):
    """A custom PDFino template for the DISCOVER-US documents."""

    margins = Margins(SIDE_MARGIN, SIDE_MARGIN, SIDE_MARGIN, SIDE_MARGIN)
    font_size = BASE_FONT_SIZE
    line_height = 1.45
    fonts = [
        Font(
            "NotoSans",
            default=True,
            normal=FONTS_PATH / "NotoSans-Regular.ttf",
            bold=FONTS_PATH / "NotoSans-Bold.ttf",
            italic=FONTS_PATH / "NotoSans-Italic.ttf",
        ),
    ]
    styles: list[Style] = [
        Style("body", options={"color": TEXT_COLOR}),
        Style("p", options={"align": "justify", "margins": Margins(2 * mm, 0, 2 * mm, 0)}),
        Style("italic", parent="p", font_name="NotoSans-Italic"),
        Style("statement", parent="italic", options={"color": TEXT_LIGHT_COLOR}),
        Style(
            "h1",
            font_name="NotoSans-Bold",
            font_size=BASE_FONT_SIZE * 2.5,
            line_height=1.15,
            options={"color": TEXT_COLOR, "margins": Margins(0, 0, 20 * mm, 0)},
        ),
        Style(
            "h2",
            parent="h2",
            font_size=11,
            line_height=1.25,
            options={"color": evan_BLUE, "margins": Margins(8 * mm, 0, 4 * mm, 0)},
        ),
        Style("h3", parent="h2", font_size=8, options={"color": TEXT_COLOR, "margins": Margins(3 * mm, 0, 3 * mm, 0)}),
    ]
