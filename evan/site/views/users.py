from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event, Session, Registration


class DashboardView(generic.TemplateView):
    template_name = "users/dashboard.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user_id = self.request.user.id
        context = super().get_context_data(**kwargs)
        context["events"] = Event.objects.filter(acl__user_id=user_id).order_by("-start_date")
        context["sessions"] = Session.objects.filter(acl__user_id=user_id).order_by("-date")
        context["registrations"] = (
            Registration.objects.filter(user_id=user_id).select_related("event").order_by("-created_at")
        )
        return context
