import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django_countries import countries
from os import environ

from toucon.models import Conference, Profile, Registration


class RegistrationRedirectView(generic.DetailView):
    template_name = 'app/registration/index.html'

    def get_object(self, queryset=None) -> Conference:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Conference, code=self.kwargs.get('code'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            registration = self.get_object().registrations.get(user=request.user)
            return redirect(registration.get_absolute_url())
        except Registration.DoesNotExist as e:
            pass
        return super().dispatch(request, *args, **kwargs)


class RegistrationView(generic.DetailView):
    template_name = 'app/registration/index.html'

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get('uuid'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().editable_by_user(request.user):
            messages.error(request, 'You don\'t have the necessary permissions to update this registration.')
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries_json'] = json.dumps(dict(countries))
        context['dietary_choices'] = Profile.DIETARY_CHOICES
        context['stripe_publishable_key'] = environ.get('STRIPE_PUBLISHABLE_KEY')
        return context
