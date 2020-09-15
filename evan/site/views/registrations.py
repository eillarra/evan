from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event, Registration, Coupon
from evan.site.emails.registrations import PaymentReminderEmail
from evan.site.pdfs.registrations import CertificatePdfMaker, ReceiptPdfMaker
from evan.tools.payments.ingenico import Ingenico


class RegistrationRedirectView(generic.DetailView):
    model = Event
    template_name = "app/registrations/index.html"

    def get_object(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Event, code=self.kwargs.get("code"))
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
            messages.error(request, "Registrations are not open for this event.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class RegistrationView(generic.DetailView):
    model = Registration
    template_name = "app/registrations/index.html"

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()

        if not registration.editable_by_user(request.user):
            messages.error(
                request, "You don't have the necessary permissions to update this registration.",
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.get_object().event
        return context


class RegistrationPaymentBaseView(generic.TemplateView):
    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    def get_ingenico_result_url(self) -> str:
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        registration = self.get_object()
        ingenico = Ingenico(
            pspid=registration.event.wbs_element,
            salt=registration.event.ingenico_salt,
            test_mode=registration.event.test_mode,
        )
        ingenico_parameters = {
            "AMOUNT": registration.remaining_fee,
            "ORDERID": registration.id,
            "RESULTURL": self.get_ingenico_result_url(),
        }
        context = super().get_context_data(**kwargs)
        context["registration"] = registration
        context["event"] = registration.event
        context["ingenico_url"] = ingenico.get_url()
        context["ingenico_parameters"] = ingenico.process_parameters(ingenico_parameters, registration.user)
        return context


class RegistrationPaymentView(RegistrationPaymentBaseView):
    """
    Perform payments using `payment.ugent.be` or coupons.
    """

    template_name = "app/registrations/payment/registration_payment_form.html"

    def get_ingenico_result_url(self) -> str:
        return self.get_object().get_payment_result_url()

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if not registration.editable_by_user(request.user):
            messages.error(request, "You don't have the necessary permissions to update this registration.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Check if the selected coupon is valid and update registration.
        """
        registration = self.get_object()
        try:
            coupon = Coupon.objects.get(code=request.POST.get("coupon"), event_id=registration.event_id)
            registration.coupon = coupon
            registration.save()
            messages.success(request, "Your coupon has been correctly applied.")
        except Coupon.DoesNotExist:
            messages.error(
                request, "Please check your coupon code. We can't find the one you've introduced.",
            )
        except IntegrityError:
            messages.error(
                request, "Sorry but the coupon you have introduced has already been used.",
            )
        except Exception as e:
            messages.error(request, "Error %s (%s)" % (e.message, type(e).__name__))
        return redirect(registration.get_payment_url())


class RegistrationPaymentDelegatedView(RegistrationPaymentBaseView):
    """
    Allows third parties to pay for a registration, without login.
    """

    template_name = "app/registrations/payment/registration_payment_delegated_form.html"

    def get_ingenico_result_url(self) -> str:
        return self.get_object().get_payment_delegated_result_url()

    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if registration.secret != kwargs.get("secret"):
            messages.error(request, "You don't have access to this registration.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RegistrationPaymentResultBaseView(generic.TemplateView):
    """
    Perform actions depending on the result of the payment process.
    """

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        status = request.GET.get("STATUS")

        # Success
        if status in Ingenico.SUCCESS_STATUSES:
            if Ingenico.validate_out_parameters(request.GET, outsalt=registration.event.ingenico_salt):
                registration.paid = registration.paid + int(request.GET.get("AMOUNT"))
                registration.save()
                messages.success(request, "Your payment was succesful.")
            else:
                messages.error(request, "Invalid query parameters.")

        # Exception
        elif status in Ingenico.EXCEPTION_STATUSES:
            messages.warning(
                request, "We will revise your payment and let you know when it is authorized.",
            )

        # Decline
        elif status in Ingenico.DECLINE_STATUSES:
            messages.error(request, "Your payment was declined.")

        # Cancel
        elif status in Ingenico.CANCEL_STATUSES:
            messages.warning(request, "Your payment has been canceled.")

        # ...and redirect
        return redirect(self.get_redirect_url())


class RegistrationPaymentResultView(RegistrationPaymentResultBaseView):
    def get_redirect_url(self) -> str:
        return self.get_object().get_payment_url()


class RegistrationPaymentDelegatedResultView(RegistrationPaymentResultBaseView):
    def get_redirect_url(self) -> str:
        return reverse("done")


class RegistrationInvoiceRequestView(generic.RedirectView):
    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if not registration.editable_by_user(request.user):
            messages.error(request, "You don't have the necessary permissions to update this registration.")
            raise PermissionDenied
        if not registration.event.allows_invoices:
            messages.error(request, "We cannot issue invoices for this event.")
            raise PermissionDenied
        registration.invoice_requested = True
        registration.save()
        PaymentReminderEmail(instance=registration).send()
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.get_object().get_payment_url()


class RegistrationPdfView(generic.View):
    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if not registration.viewable_by_user(request.user) and not request.user.is_staff:
            messages.error(request, "You don't have the necessary permissions to view this file.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RegistrationCertificatePdf(RegistrationPdfView):
    """
    Download a certificate in PDF format.
    """

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        maker = CertificatePdfMaker(registration=obj, filename=f"receipt--{obj.uuid}.pdf", as_attachment=False)
        return maker.response


class RegistrationReceiptPdf(RegistrationPdfView):
    """
    Download a receipt in PDF format.
    """

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        maker = ReceiptPdfMaker(registration=obj, filename=f"receipt--{obj.uuid}.pdf", as_attachment=False)
        return maker.response
