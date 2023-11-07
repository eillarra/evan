import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, SimpleDocTemplate


FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
pdfmetrics.registerFont(TTFont("Roboto Light", os.path.join(FONTS_DIR, "IBMPlexSans-Light.ttf")))
pdfmetrics.registerFont(TTFont("Roboto Regular", os.path.join(FONTS_DIR, "IBMPlexSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Roboto Medium", os.path.join(FONTS_DIR, "IBMPlexSans-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Roboto Bold", os.path.join(FONTS_DIR, "IBMPlexSans-SemiBold.ttf")))


class Wrapdf:
    def __init__(self, *, page_size: tuple = A4, margins: list[float] | None = None) -> None:
        if not margins:
            margins = [3.5, 2, 3, 2]

        self.buffer = io.BytesIO()
        self.parts = []
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=page_size,
            topMargin=margins[0] - 6,  # compensate inner Frame padding (6 points)
            rightMargin=margins[1] - 6,
            bottomMargin=margins[2] - 6,
            leftMargin=margins[3] - 6,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.buffer.close()

    def _first_page(self, canvas, doc) -> None:
        pass

    def _later_pages(self, canvas, doc) -> None:
        pass

    def add_page_break(self) -> None:
        self.parts.append(PageBreak())

    def get(self):
        self.doc.build(self.parts, onFirstPage=self._first_page, onLaterPages=self._later_pages)
        return self.buffer.getvalue()
