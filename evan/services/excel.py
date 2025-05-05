"""A module for generating Excel files from Django querysets."""

from io import BytesIO

import polars as pl
import xlsxwriter
from django.db.models import QuerySet
from django.http import HttpResponse
from django.views import View


type DataSheet = tuple[pl.DataFrame, str]


def set_column_types(df: pl.DataFrame) -> pl.DataFrame:
    """Set correct column types for Excel export based on schema detection."""
    for col in df.columns:
        dtype = df[col].dtype

        if dtype in {pl.Int8, pl.Int16, pl.Int32, pl.Int64}:
            df = df.with_columns(pl.col(col).cast(pl.Int32, strict=False))
        elif dtype in {pl.Float32, pl.Float64}:
            df = df.with_columns(pl.col(col).cast(pl.Float32, strict=False))
        elif dtype == pl.Boolean:
            df = df.with_columns(pl.col(col).cast(pl.Boolean, strict=False))
        elif dtype in {pl.Date, pl.Datetime}:
            # No need to cast date and datetime columns as Polars already handles these types correctly for Excel export
            continue
        else:
            df = df.with_columns(pl.col(col).cast(pl.Utf8, strict=False))

    return df


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

    filename: str
    queryset: QuerySet
    fields: list[str]

    def get_filename(self) -> str:
        """Get the filename, without extension."""
        return self.filename

    def get_queryset(self) -> QuerySet:
        """Get the queryset."""
        return self.queryset

    def get_sheet(self, sheet_name: str = "Data") -> DataSheet:
        """Get the default Polars DataFrame, based on queryset and fields, as a DataSheet."""
        return pl.DataFrame(list(self.get_queryset().values(*self.fields))), sheet_name

    def get_sheets(self) -> list[DataSheet]:
        """Get the Excel file sheets, as a list of tuples of Polars DataFrames and sheet names."""
        return [self.get_sheet()]

    def get(self, request, *args, **kwargs) -> ExcelResponse:
        """Generate an Excel file with all the sheets.

        :returns: An `ExcelResponse` object representing the generated Excel file.
        """
        buffer = BytesIO()
        sheet_names = set()

        with pl.Config(float_precision=2), xlsxwriter.Workbook(buffer) as workbook:
            for df, sheet_name in self.get_sheets():
                while sheet_name in sheet_names:
                    sheet_name += "_"
                set_column_types(df).write_excel(workbook=workbook, worksheet=sheet_name)
                sheet_names.add(sheet_name)

        buffer.seek(0)  # rewind the buffer

        return ExcelResponse(buffer.read(), filename=f"{self.get_filename()}.xlsx")
