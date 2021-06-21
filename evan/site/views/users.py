from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import generic


class DashboardView(generic.TemplateView):
    template_name = "app/dashboard/index.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
