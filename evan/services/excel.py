from tempfile import NamedTemporaryFile

from django.http import HttpResponse
from openpyxl import Workbook


class ExcelResponse(HttpResponse):
    def __init__(self, *args, filename: str = "", **kwargs):
        kwargs.setdefault(
            "content_type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"
        )
        super().__init__(*args, **kwargs)
        self["Content-Disposition"] = f'attachment; filename="{filename}"'


class ModelExcelWriter:
    def __init__(self, *, queryset, filename: str):
        self.queryset = queryset
        self.filename = filename
        self.workbook = None

    def get_sheets(self) -> list[dict]:
        raise NotImplementedError

    def set_custom_styles(self) -> None:
        pass

    @property
    def response(self) -> ExcelResponse:
        self.workbook = Workbook()
        del self.workbook["Sheet"]

        for sheet in self.get_sheets():
            ws = self.workbook.create_sheet(title=sheet["title"])
            for entry in sheet["data"]:
                ws.append(entry)

        self.set_custom_styles()

        with NamedTemporaryFile() as tmp:
            self.workbook.save(tmp.name)
            tmp.seek(0)
            stream = tmp.read()

        return ExcelResponse(stream, filename=self.filename)
