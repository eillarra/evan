from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event, Registration, Coupon
from evan.tools.payments.ingenico import Ingenico


class RegistrationRedirectView(generic.DetailView):
    model = Event
    template_name = 'app/registrations/index.html'

    def get_object(self, queryset=None) -> Event:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Event, code=self.kwargs.get('code'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()

        try:
            registration = event.registrations.get(user=request.user)
            return redirect(registration.get_absolute_url())
        except Registration.DoesNotExist:
            pass

        if not event.is_open_for_registration:
            messages.error(request, 'Registrations are not open for this event.')
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class RegistrationView(generic.DetailView):
    model = Registration
    template_name = 'app/registrations/index.html'

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get('uuid'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()

        if not registration.editable_by_user(request.user):
            messages.error(request, 'You don\'t have the necessary permissions to update this registration.')
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.get_object().event
        return context


class RegistrationPaymentView(generic.TemplateView):
    """
    Perform payments using `payment.ugent.be` or coupons.
    """
    template_name = 'app/registrations/payment/registration_payment_form.html'
    registration = ''

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get('uuid'))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if not registration.editable_by_user(request.user):
            messages.error(request, 'You don\'t have the necessary permissions to update this registration.')
            raise PermissionDenied
        if not registration.is_paid and registration.invoice_requested:
            messages.error(request, 'You requested an invoice before. Contact us first if you want to pay by card.')
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        registration = self.get_object()
        ingenico = Ingenico(
            pspid=registration.event.wbs_element,
            salt=registration.event.ingenico_salt,
            test_mode=registration.event.test_mode
        )
        ingenico_parameters = {
            'AMOUNT': registration.remaining_fee,
            'ORDERID': registration.id,
            'RESULTURL': registration.get_payment_result_url(),
        }
        context = super().get_context_data(**kwargs)
        context['registration'] = registration
        context['event'] = registration.event
        context['ingenico_url'] = ingenico.get_url()
        context['ingenico_parameters'] = ingenico.process_parameters(ingenico_parameters, self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        """
        Check if the selected coupon is valid and update registration.
        """
        registration = self.get_object()
        try:
            coupon = Coupon.objects.get(code=request.POST.get('coupon'), event_id=registration.event_id)
            registration.coupon = coupon
            registration.save()
            messages.success(request, 'Your coupon has been correctly applied.')
        except Coupon.DoesNotExist:
            messages.error(request, 'Please check your coupon code. We can\'t find the one you\'ve introduced.')
        except IntegrityError:
            messages.error(request, 'Sorry but the coupon you have introduced has already been used.')
        except Exception as e:
            messages.error(request, 'Error %s (%s)' % (e.message, type(e).__name__))
        return redirect(registration.get_payment_url())


class RegistrationPaymentResultView(generic.TemplateView):
    """
    Perform actions depending on the result of the payment process.
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = get_object_or_404(Registration, uuid=self.kwargs.get('uuid'))
        status = request.GET.get('STATUS')

        # Success
        if status in Ingenico.SUCCESS_STATUSES:
            registration.paid = registration.paid + int(request.GET.get('AMOUNT'))
            registration.save()
            messages.success(request, 'Your payment was succesful.')
            """
            if Ingenico(salt=registration.event.ingenico_salt).validate_query_parameters(request.GET):
                registration.paid = registration.paid + int(request.GET.get('AMOUNT'))
                registration.save()
                messages.success(request, 'Your payment was succesful.')
            else:
                messages.error(request, 'Invalid query parameters.')
            """
        # Exception
        elif status in Ingenico.EXCEPTION_STATUSES:
            messages.warning(request, 'We will revise your payment and let you know when it is authorized.')
        # Decline
        elif status in Ingenico.DECLINE_STATUSES:
            messages.error(request, 'Your payment was declined.')
        # Cancel
        elif status in Ingenico.CANCEL_STATUSES:
            messages.warning(request, 'Your payment has been canceled.')

        # ...and redirect
        return redirect(registration.get_payment_url())


class RegistrationReceipt(generic.DetailView):
    model = Registration
    template_name = 'app/registrations/payment/registration_receipt.html'

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get('uuid'))
        return self.object
