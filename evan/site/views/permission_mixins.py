from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse as HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View


class PermissionMixin(View):
    """Mixin to check if the user is logged in and has the necessary permissions."""

    group: str

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name=self.group).exists():
            messages.error(request, "You don't have the necessary permissions to view this page.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class ManagementPermissionMixin(PermissionMixin):
    group = "Management"


class SteeringCommitteePermissionMixin(PermissionMixin):
    group = "Steering Committee"
