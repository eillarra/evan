from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic
from wkhtmltopdf.views import PDFTemplateResponse

from toucon.models import Conference


class ConferenceView(generic.DetailView):
    template_name = 'app/conference/index.html'

    def get_object(self, queryset=None) -> Conference:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Conference, code=self.kwargs.get('code'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().editable_by_user(request.user):
            messages.error(request, 'You don\'t have the necessary permissions to manage this conference.')
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ConferenceBadgesView(ConferenceView):
    def get(self, request, *args, **kwargs):
        conference = self.get_object()
        registrations = conference.registrations.select_related('user__profile') \
                                  .order_by('user__{0}'.format(conference.json_badge['order_by']))
        if 'r' in request.GET:
            registrations = registrations.filter(uuid__in=[request.GET['r']])

        return PDFTemplateResponse(
            request=request,
            template='badges/standard.pdf.html',
            filename='{0}-badges.pdf'.format(conference.code),
            context={
                'conference': conference,
                'registrations': registrations,
            },
            cmd_options={
                'margin-right': 0,
                'margin-left': 0,
            },
            show_content_in_browser=True
        )
