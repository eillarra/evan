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
from evan.site.views.file_makers.registrations import CertificatePdfMaker, ReceiptPdfMaker

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


def _finalize_payment_attempt(registration: Registration, query_params: QueryDict, *, status: str) -> bool:
    """Persist terminal non-success states for the current payment attempt.

    Rejects feedback that does not carry a valid Worldline SHA-OUT signature, so
    decline/cancel transitions are as tamper-proof as the success path handled
    by ``_credit_worldline_payment``.

    :param registration: registration to update.
    :param query_params: callback querystring.
    :param status: terminal attempt status to persist.
    :returns: True only when the attempt was actually transitioned out of PENDING.
    """
    if not UGentBridge.validate_out_parameters(query_params, outsalt=registration.event.ugent_bridge.get("salt")):
        return False

    order_id = query_params.get("ORDERID", "")
    if not order_id:
        return False

    with transaction.atomic():
        try:
            attempt = RegistrationPaymentAttempt.objects.select_for_update().get(order_id=order_id)
        except RegistrationPaymentAttempt.DoesNotExist:
            return False

        if attempt.registration_id != registration.id:
            return False
        if attempt.status != RegistrationPaymentAttempt.PENDING:
            return False

        attempt.mark_resolved(status=status, payid=query_params.get("PAYID", ""), callback_data=query_params.dict())
        attempt.save(update_fields=["status", "payid", "callback_data", "resolved_at"])

    return True


def _rotate_payment_hash(registration: Registration) -> None:
    """Rotate the registration's unique_hash so the next attempt gets a fresh ORDERID.

    :param registration: The registration whose payment hash should rotate.
    """
    registration.unique_hash = registration.generate_unique_hash()
    registration.save(update_fields=["unique_hash"])


@method_decorator(csrf_exempt, name="dispatch")
class RegistrationPaymentResultBaseView(TemplateView):
    """Process Worldline payment outcome over the same URL.

    The UGent bridge / Worldline back office is configured with this URL as
    ACCEPTURL / DECLINEURL / CANCELURL / EXCEPTIONURL, and UGent's Pay reuses
    it for both feedback channels:

    - Browser redirect (GET): Worldline returns the user here after the payment
      session. We finalise the attempt, surface a user-facing message, and
      redirect back to the registration's payment page.
    - Asynchronous server-to-server feedback (POST): UGent's Pay pushes status
      transitions here independently of the user's browser, so payments are
      finalised even when the user closes the browser without returning. No
      user is behind the request, so we acknowledge with HTTP 200 and skip the
      message/redirect.
    """

    def get_object(self, queryset=None) -> Registration:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Registration, uuid=self.kwargs.get("uuid"))
        return self.object

    def dispatch(self, request, *args, **kwargs):
        registration = self.get_object()
        # Worldline delivers browser redirects as GET with query params and
        # server-to-server feedback as POST with a form-encoded body. Read the
        # status from the right container per method.
        query_params = request.POST if request.method == "POST" else request.GET
        status = query_params.get("STATUS")

        credited = self._process_status(registration, query_params, status)

        if request.method == "POST":
            # Async server-to-server feedback: acknowledge receipt, no user to
            # message or redirect.
            return HttpResponse(status=200)

        # Browser redirect: surface a user-facing message and redirect back.
        if status in UGentBridge.SUCCESS_STATUSES:
            if credited:
                messages.success(request, "Your payment was successful.")
            elif registration.is_paid:
                messages.success(request, "Your payment was already registered.")
            else:
                messages.error(request, "Invalid query parameters.")
        elif status in UGentBridge.EXCEPTION_STATUSES:
            messages.warning(request, "We will revise your payment and let you know when it is authorised.")
        elif status in UGentBridge.DECLINE_STATUSES:
            messages.error(request, "Your payment was declined.")
        elif status in UGentBridge.CANCEL_STATUSES:
            messages.warning(request, "Your payment was canceled.")
        return redirect(self.get_redirect_url())  # type: ignore

    def _process_status(self, registration: Registration, query_params: QueryDict, status: str | None) -> bool:
        """Apply the terminal action for a Worldline status, if any.

        :param registration: registration the feedback belongs to.
        :param query_params: GET or POST params carrying the Worldline payload.
        :param status: Worldline STATUS code from the feedback.
        :returns: True only when this call credited a new payment.
        """
        if status in UGentBridge.SUCCESS_STATUSES:
            return _credit_worldline_payment(registration, query_params)
        if status in UGentBridge.DECLINE_STATUSES:
            finalised = _finalize_payment_attempt(registration, query_params, status=RegistrationPaymentAttempt.FAILED)
            # Rotate hash so a retry uses a fresh ORDERID; some Worldline
            # configurations reject resubmitting a previously declined ORDERID.
            if finalised:
                _rotate_payment_hash(registration)
            return False
        if status in UGentBridge.CANCEL_STATUSES:
            finalised = _finalize_payment_attempt(
                registration, query_params, status=RegistrationPaymentAttempt.CANCELLED
            )
            # Rotate hash so a retry uses a fresh ORDERID; Worldline registers the
            # ORDERID the moment the form is submitted, so cancelling leaves it
            # "used" and a second attempt with the same ORDERID is rejected.
            if finalised:
                _rotate_payment_hash(registration)
            return False
        # EXCEPTION (52/92) and INVALID (0) carry no terminal action here:
        # EXCEPTION means the payment is under Worldline review and may still
        # flip either way, so admin must confirm the outcome before clearing.
        return False


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
        maker = CertificatePdfMaker(registration=obj, as_attachment=False)
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
        maker = ReceiptPdfMaker(registration=obj, as_attachment=False)
        return maker.response
