from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView, TemplateView, View

from evan.api.serializers.events import EventSerializer
from evan.api.serializers.sessions import SessionReadOnlySerializer
from evan.api.serializers.users import UserSerializer
from evan.models import Coupon, Event, Registration, RegistrationPaymentAttempt
from evan.services.mailer.registrations import schedule_registration_email
from evan.services.payments.ugent_bridge import UGentBridge
from evan.site.views.file_makers.pdf import CertificatePdfMaker
from evan.site.views.file_makers.receipt import ReceiptPdfMaker

from .inertia import InertiaView


class RegistrationRedirectView(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            registration = Registration.objects.get(uuid=self.kwargs.get("uuid"))
            return redirect(registration.event.get_registration_url())
        except Registration.DoesNotExist as exc:
            raise Http404 from exc


class RegistrationView(InertiaView):
    is_after_event = False
    vue_entry_point = "apps/registration/main.ts"

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(
                Event.objects.prefetch_related(
                    "files",
                    "fees",
                    "sessions",
                    "sessions__topics",
                    "sessions__subsessions",
                    "sponsors",
                    "sponsors__files",
                    "topics",
                    "tracks",
                    "venues__rooms",
                ),
                code=self.kwargs.get("code"),
            )
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_event().is_open_for_registration:
            # check if the user has a registration for this event
            if not Registration.objects.filter(event=self.get_event(), user=request.user).exists():
                messages.error(request, "Registrations are not open for this event.")
                raise PermissionDenied
            if self.get_event().is_closed:
                self.is_after_event = True
        return super().dispatch(request, *args, **kwargs)

    def get_vue_entry_point(self, request, *args, **kwargs) -> str:
        if self.is_after_event:
            return "apps/registrationAfter/main.ts"
        return self.vue_entry_point

    def get_props(self, request, *args, **kwargs) -> dict:
        event = self.get_event()
        sessions = event.sessions.all()  # type: ignore
        return {
            "user": UserSerializer(request.user, context={"request": request}).data,
            "event": EventSerializer(event, context={"request": request}).data,
            "sessions": SessionReadOnlySerializer(sessions, many=True, context={"request": request}).data,
        }

    def get_page_title(self, request, *args, **kwargs) -> str:
        return f"Registration - {self.get_event().name} - Evan"


class RegistrationPaymentBaseView(TemplateView):
    def get_or_create_payment_attempt(self, registration: Registration) -> RegistrationPaymentAttempt | None:
        """Return the active deterministic payment attempt for the current payment form.

        :param registration: The registration being paid.
        :returns: The persisted payment attempt, or None when no payment is needed.
        """
        if registration.is_paid or registration.remaining_fee <= 0:
            return None

        expected_amount = registration.remaining_fee
        order_id = UGentBridge.generate_order_id(registration.pk, expected_amount, registration.unique_hash)

        attempt, _ = RegistrationPaymentAttempt.objects.get_or_create(
            order_id=order_id,
            defaults={
                "registration": registration,
                "expected_amount": expected_amount,
            },
        )
        return attempt

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().event.allows_payments:
            messages.error(request, "Payments are not active for this event.")
            raise PermissionDenied

        if not self.get_object().is_accepted:
            messages.error(request, "Your registration has not been accepted.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration.objects.select_related("event"), uuid=self.kwargs.get("uuid"))
        return self.object

    def get_worldline_result_url(self) -> str:
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        registration = self.get_object()
        payment_attempt = self.get_or_create_payment_attempt(registration)
        worldline = UGentBridge(
            pspid=registration.event.ugent_bridge.get("wbs_element"),
            salt=registration.event.ugent_bridge.get("salt"),
            test_mode=registration.event.ugent_bridge.get("test_mode"),
        )
        worldline_parameters = {
            "AMOUNT": registration.remaining_fee,
            "ORDERID": registration.pk,
            "CALLBACKURL": registration.get_payment_callback_url(),
            "RESULTURL": self.get_worldline_result_url(),
        }
        context = super().get_context_data(**kwargs)
        context["registration"] = registration
        context["event"] = registration.event
        context["worldline_url"] = worldline.get_url()
        context["payment_attempt"] = payment_attempt
        context["worldline_parameters"] = worldline.process_parameters(
            worldline_parameters, registration.user, registration.unique_hash, paramvar=str(registration.uuid)
        )
        return context


class RegistrationPaymentView(RegistrationPaymentBaseView):
    """
    Perform payments using `payment.ugent.be` or coupons.
    """

    template_name = "registrations/payments/registration_payment_form.html"

    def get_worldline_result_url(self) -> str:
        return self.get_object().get_payment_result_url()

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().editable_by_user(request.user):
            messages.error(request, "You don't have the necessary permissions to update this registration.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Check if the selected coupon is valid and update registration.
        """
        registration = self.get_object()
        try:
            coupon = Coupon.objects.get(code=request.POST.get("coupon"), event_id=registration.event_id)  # type: ignore
            registration.coupon = coupon  # type: ignore
            registration.save()
            messages.success(request, "Your coupon has been correctly applied.")
        except Coupon.DoesNotExist:
            messages.error(request, "Please check your coupon code. We can't find the one you've introduced.")
        except IntegrityError:
            messages.error(request, "Sorry but the coupon you have introduced has already been used.")
        except Exception as exc:
            messages.error(request, f"Error {exc.message} ({type(exc).__name__})")  # type: ignore
        return redirect(registration.get_payment_url())


class RegistrationPaymentDelegatedView(RegistrationPaymentBaseView):
    """
    Allows third parties to pay for a registration, without login.
    """

    template_name = "registrations/payments/registration_payment_delegated_form.html"

    def get_worldline_result_url(self) -> str:
        return self.get_object().get_payment_delegated_result_url()

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().secret != kwargs.get("secret"):
            messages.error(request, "You don't have access to this registration.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def _credit_worldline_payment(registration: Registration, query_params: QueryDict) -> bool:
    """Credit a Worldline payment to a registration if valid and not already processed.

    :param registration: The registration to credit the payment to.
    :param query_params: The query dict from the Worldline callback (GET params).
    :returns: True if the payment was credited, False otherwise.
    """
    payid = query_params.get("PAYID", "")
    order_id = query_params.get("ORDERID", "")
    if not payid or not order_id:
        return False
    if not UGentBridge.validate_out_parameters(query_params, outsalt=registration.event.ugent_bridge.get("salt")):
        return False

    try:
        amount = int(float(query_params.get("AMOUNT", 0)))
    except TypeError, ValueError:
        return False

    with transaction.atomic():
        locked_registration = Registration.objects.select_for_update().get(pk=registration.pk)
        try:
            attempt = RegistrationPaymentAttempt.objects.select_for_update().get(order_id=order_id)
        except RegistrationPaymentAttempt.DoesNotExist:
            return False

        if attempt.registration_id != locked_registration.id:
            return False
        if attempt.status != RegistrationPaymentAttempt.PENDING:
            return False
        if attempt.expected_amount != amount:
            return False
        if RegistrationPaymentAttempt.objects.exclude(pk=attempt.pk).filter(payid=payid).exists():
            return False

        attempt.mark_resolved(
            status=RegistrationPaymentAttempt.SUCCEEDED,
            payid=payid,
            callback_data=query_params.dict(),
        )
        attempt.save(update_fields=["status", "payid", "callback_data", "resolved_at"])

        locked_registration.paid = locked_registration.paid + amount
        locked_registration.payid = payid
        # Rotate the hash so any future payment attempt gets a fresh ORDERID.
        # Worldline marks the ORDERID as permanently used after a successful payment.
        locked_registration.unique_hash = locked_registration.generate_unique_hash()
        locked_registration.save()
        registration.paid = locked_registration.paid
        registration.payid = locked_registration.payid
        registration.unique_hash = locked_registration.unique_hash
        registration.saldo = locked_registration.saldo
        return True


def _finalize_payment_attempt(registration: Registration, query_params: QueryDict, *, status: str) -> None:
    """Persist terminal non-success states for the current payment attempt.

    :param registration: The registration being updated.
    :param query_params: The callback querystring.
    :param status: The terminal attempt status to persist.
    """
    order_id = query_params.get("ORDERID", "")
    if not order_id:
        return

    with transaction.atomic():
        try:
            attempt = RegistrationPaymentAttempt.objects.select_for_update().get(order_id=order_id)
        except RegistrationPaymentAttempt.DoesNotExist:
            return

        if attempt.registration_id != registration.id:
            return
        if attempt.status != RegistrationPaymentAttempt.PENDING:
            return

        attempt.mark_resolved(status=status, payid=query_params.get("PAYID", ""), callback_data=query_params.dict())
        attempt.save(update_fields=["status", "payid", "callback_data", "resolved_at"])


def _rotate_payment_hash(registration: Registration) -> None:
    """Rotate the registration's unique_hash so the next attempt gets a fresh ORDERID.

    :param registration: The registration whose payment hash should rotate.
    """
    registration.unique_hash = registration.generate_unique_hash()
    registration.save(update_fields=["unique_hash"])


class RegistrationPaymentResultBaseView(TemplateView):
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
        if status in UGentBridge.SUCCESS_STATUSES:
            if _credit_worldline_payment(registration, request.GET):
                messages.success(request, "Your payment was succesful.")
            elif registration.is_paid:
                messages.success(request, "Your payment was already registered.")
            else:
                messages.error(request, "Invalid query parameters.")

        # Exception
        elif status in UGentBridge.EXCEPTION_STATUSES:
            messages.warning(request, "We will revise your payment and let you know when it is authorized.")

        # Decline
        elif status in UGentBridge.DECLINE_STATUSES:
            _finalize_payment_attempt(registration, request.GET, status=RegistrationPaymentAttempt.FAILED)
            # Rotate hash so a retry uses a fresh ORDERID; some Worldline configurations
            # reject resubmitting a previously declined ORDERID.
            _rotate_payment_hash(registration)
            messages.error(request, "Your payment was declined.")

        # Cancel
        elif status in UGentBridge.CANCEL_STATUSES:
            _finalize_payment_attempt(registration, request.GET, status=RegistrationPaymentAttempt.CANCELLED)
            # Rotate hash so a retry uses a fresh ORDERID; Worldline registers the
            # ORDERID the moment the form is submitted, so cancelling leaves it
            # "used" and a second attempt with the same ORDERID is rejected.
            _rotate_payment_hash(registration)
            messages.warning(request, "Your payment has been canceled.")

        # ...and redirect
        return redirect(self.get_redirect_url())  # type: ignore


@method_decorator(csrf_exempt, name="dispatch")
class RegistrationPaymentCallbackView(View):
    """Server-to-server callback from Worldline for confirmed payments.

    This is the target of Worldline's account-level "Direct HTTP
    server-to-server request" feedback, configured per WBS element in the
    Worldline back office with a `<PARAMVAR>`-templated URL (see
    ``UGentBridge.process_parameters``, which submits the registration's uuid as
    ``PARAMVAR``). Worldline calls it directly, bypassing the user's browser,
    for every status transition - so it ensures payments are credited (and
    declines/cancels rotate the hash) even when the browser never makes it
    back to the result URL. The back office lets the merchant choose GET or
    POST delivery, so both methods are handled identically here.
    """

    def get(self, request, *args, **kwargs):
        return self._handle(request, request.GET)

    def post(self, request, *args, **kwargs):
        return self._handle(request, request.POST)

    def _handle(self, request, query_params: QueryDict) -> HttpResponse:
        """Process the Worldline server-to-server notification.

        Ignoring cancel/decline notifications leaves the matching payment
        attempt PENDING with an ORDERID Worldline has already registered,
        which blocks retries until an admin regenerates the hash.

        :param query_params: The notification parameters, from either GET or POST.
        :returns: An empty 200 response, acknowledging receipt to Worldline.
        """
        registration = get_object_or_404(Registration.objects.select_related("event"), uuid=self.kwargs.get("uuid"))
        status = query_params.get("STATUS")

        if status in UGentBridge.SUCCESS_STATUSES:
            _credit_worldline_payment(registration, query_params)
        elif status in UGentBridge.DECLINE_STATUSES:
            _finalize_payment_attempt(registration, query_params, status=RegistrationPaymentAttempt.FAILED)
            _rotate_payment_hash(registration)
        elif status in UGentBridge.CANCEL_STATUSES:
            _finalize_payment_attempt(registration, query_params, status=RegistrationPaymentAttempt.CANCELLED)
            _rotate_payment_hash(registration)
        # Exception and invalid statuses: no action here. The result view's
        # browser-side redirect handles exception messaging; invalid statuses
        # carry no useful signal.
        return HttpResponse(status=200)


class RegistrationPaymentResultView(RegistrationPaymentResultBaseView):
    def get_redirect_url(self) -> str:
        return self.get_object().get_payment_url()


class RegistrationPaymentDelegatedResultView(RegistrationPaymentResultBaseView):
    def get_redirect_url(self) -> str:
        return reverse("done")


class RegistrationInvoiceRequestView(RedirectView):
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
        if not registration.is_accepted:
            messages.error(request, "Your registration has not been accepted.")
            raise PermissionDenied
        if not registration.event.allows_invoices:
            messages.error(request, "We cannot issue invoices for this event.")
            raise PermissionDenied
        if registration.is_paid:
            messages.info(request, "Your registration is already paid.")
            return super().dispatch(request, *args, **kwargs)
        if registration.invoice_requested:
            messages.info(request, "Invoice was already requested.")
            return super().dispatch(request, *args, **kwargs)
        updated_count = Registration.objects.filter(pk=registration.pk, invoice_requested=False).update(
            invoice_requested=True
        )
        if updated_count == 0:
            messages.info(request, "Invoice was already requested.")
            return super().dispatch(request, *args, **kwargs)

        registration.invoice_requested = True
        schedule_registration_email(registration, code="registration.payment_reminder")
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.get_object().get_payment_url()


class RegistrationPdfView(View):
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

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        if not registration.is_paid:
            messages.error(request, "Receipt is not available.")
            raise PermissionDenied
        if registration.paid == 0:
            messages.error(request, "Receipt is only available for credit card payments.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        maker = ReceiptPdfMaker(registration=obj, filename=f"receipt--{obj.uuid}.pdf", as_attachment=False)
        return maker.response
