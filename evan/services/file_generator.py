from io import BytesIO
from typing import TYPE_CHECKING

import polars as pl
from django.db.models import QuerySet
from django.http import HttpResponse
from django.views import View
from pdfino.django import PdfResponse


if TYPE_CHECKING:
    from pdfino import Document


class ExcelResponse(HttpResponse):
    """An HTTP response class that will send Excel content."""

    def __init__(self, *args, filename: str = "", **kwargs):
        kwargs.setdefault(
            "content_type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"
        )
        super().__init__(*args, **kwargs)
        self["Content-Disposition"] = f'attachment; filename="{filename}"'


class ExcelView(View):
    """A view that generates an Excel file.

    :param queryset: The queryset to convert to Excel.
    :param columns: The columns to include in the Excel file.
    :param filename: The name of the file (without extension).
    """

    queryset: QuerySet
    fields: list[str]
    filename: str

    def get_queryset(self) -> QuerySet:
        """Get the queryset."""
        return self.queryset

    def get_dataframe(self) -> pl.DataFrame:
        """Get the Polars DataFrame."""
        return pl.DataFrame(list(self.get_queryset().values(*self.fields)))

    def get_filename(self) -> str:
        """Get the filename, without extension."""
        return self.filename

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """Generate an Excel file with all the sheets.

        :return: An `ExcelResponse` object representing the generated Excel file.
        """
        buffer = BytesIO()
        df = self.get_dataframe()
        df.write_excel(buffer)
        buffer.seek(0)  # rewind the buffer

        return ExcelResponse(buffer.read(), filename=f"{self.get_filename()}.xlsx")


class PdfView(View):
    filename: str
    as_attachment: bool = False

    def get_pdf_filename(self) -> str:
        """Get the PDF filename."""
        return self.filename

    def get_pdf_document(self) -> "Document":
        """Get the PDF document."""
        raise NotImplementedError

    def get(self, request, *args, **kwargs) -> PdfResponse:
        """Get the PDF response.

        :return: A `PdfResponse` object representing the generated PDF file."""
        return PdfResponse(
            content=self.get_pdf_document().bytes,
            filename=self.get_pdf_filename(),
            as_attachment=self.as_attachment,
        )
