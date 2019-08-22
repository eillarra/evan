import pyexcel as pe

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.viewsets import GenericViewSet

from rest_framework.response import Response

from evan.models import Event, Paper
from ..permissions import EventRelatedObjectPermission
from ..serializers import PaperSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet


class PapersViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer

    @action(detail=False, methods=['POST'], parser_classes=(FormParser, MultiPartParser,))
    def upload(self, request, *args, **kwargs):
        event = Event.objects.get(code=kwargs.get('code'))
        bulk_papers = []

        try:
            sheet = pe.get_sheet(file=request.data['csv'])
            sheet.name_columns_by_row(0)
        except Exception as e:
            raise ValidationError({
                'papers': [str(e)]
            })

        if 'title' not in sheet.colnames or 'authors' not in sheet.colnames:
            raise ValidationError({
                'papers': ['Invalid format: make sure the CSV includes `title` and `authors` column headers.']
            })

        for record in sheet.to_records():
            bulk_papers.append(Paper(**{**dict(record), **{'event_id': event.id}}))

        Paper.objects.bulk_create(bulk_papers)
        return Response(PaperSerializer(event.papers.all(), many=True, context={'request': request}).data)


class PaperViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer
