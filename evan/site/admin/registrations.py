from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.urls import path, reverse
from django.utils.html import format_html

from evan.models import Registration, InvitationLetter
from evan.site.emails.registrations import (
    DelegatedPaymentEmail,
    RegistrationProfileReminderEmail,
    RegistrationReminderEmail,
    PaymentReminderEmail,
    VisaReminderEmail,
)


class RegistrationIsPaidFilter(admin.SimpleListFilter):
    title = "payment status"
    parameter_name = "paid"

    def lookups(self, request, model_admin):
        return (
            ("y", "Paid"),
            ("c", "Paid, using a coupon"),
            ("n", "Not paid, no invoice"),
            ("i", "Not paid, but requested invoice"),
        )

    def queryset(self, request, queryset):
        if self.value() == "y":
            return queryset.filter(saldo__gte=0)
        elif self.value() == "c":
            return queryset.filter(saldo__gte=0, coupon__isnull=False)
        elif self.value() == "n":
            return queryset.filter(saldo__lt=0, invoice_requested=False)
        elif self.value() == "i":
            return queryset.filter(saldo__lt=0, invoice_requested=True)


class InvitationLetterInline(admin.StackedInline):
    model = InvitationLetter
    fk_name = "registration"
    extra = 0
    verbose_name = "Invitation letter"
    verbose_name_plural = "Invitation letter"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = (
        "id",
        "created_at",
        "name",
        "accepted_col",
        "fee",
        "paid_col",
        "with_coupon",
        "invoice",
        "visa",
    )
    list_filter = (
        RegistrationIsPaidFilter,
        "invoice_requested",
        "invoice_sent",
        "visa_requested",
        "visa_sent",
        ("event", admin.RelatedOnlyFieldListFilter),
        "is_accepted",
    )
    search_fields = ("id", "uuid", "user__email", "user__username", "user__first_name", "user__last_name")
    # form
    raw_id_fields = ("event", "user", "coupon")
    readonly_fields = ("event", "base_fee", "extra_fees", "paid", "saldo")
    fieldsets = (
        (
            None,
            {
                "fields": ("event", "user", "is_accepted"),
            },
        ),
        (
            "Payment",
            {
                "fields": (
                    "fee_type",
                    ("base_fee", "extra_fees"),
                    "manual_extra_fees",
                    ("paid_via_invoice", "invoice_requested", "invoice_sent"),
                    "coupon",
                    "paid",
                    "saldo",
                ),
            },
        ),
        (
            "Extra information",
            {
                "fields": ("visa_requested", "visa_sent"),
            },
        ),
    )
    inlines = (InvitationLetterInline,)
    actions = (
        "send_reminder",
        "send_visa_reminder",
        "send_payment_reminder",
        "send_delegated_payment",
        "send_profile_reminder",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user__profile", "coupon").prefetch_related("event")
        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():
            return qs
        if request.user.groups.filter(name="Administration").exists():
            return qs.filter(event__acl__user_id__exact=request.user.id)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ("base_fee", "extra_fees", "paid", "saldo")
        return self.readonly_fields

    def get_urls(self):
        my_urls = [
            path("<path:object_id>/letter/", self.pdf_letter_view, name="registration_pdf_letter"),
        ]
        return my_urls + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        extra_context = extra_context or {}
        extra_context["has_letter"] = InvitationLetter.objects.filter(registration_id=object_id).exists()
        extra_context["payment_delegated_url"] = obj.get_payment_delegated_url() if not obj.is_paid else None
        extra_context["certificate_url"] = obj.get_certificate_url() if obj.event.is_closed and obj.is_paid else None
        extra_context["receipt_url"] = obj.get_receipt_url() if obj.is_paid else None
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def pdf_letter_view(self, request, object_id, extra_context=None):
        from evan.site.views.file_makers.pdf import InvitationLetterPdfMaker

        obj = self.get_object(request, unquote(object_id))
        maker = InvitationLetterPdfMaker(registration=obj, filename=f"letter--{obj.uuid}.pdf", as_attachment=False)
        return maker.response

    def name(self, obj):
        affiliation = obj.user.profile.affiliation if obj.user.profile.affiliation else "-"
        url = reverse("admin:auth_user_changelist")
        return format_html(
            f'<a href="{url}{obj.user_id}/" target="admin_user">{obj.user.profile.name}</a>, {affiliation}'
        )

    """
    Custom fields
    """

    def accepted_col(self, obj) -> bool:
        return obj.is_accepted

    def fee(self, obj):
        return format_html(f"{obj.base_fee}&nbsp;+&nbsp;{obj.extra_fees}")

    def paid_col(self, obj) -> bool:
        return obj.is_paid

    def invoice(self, obj):
        requested = "yes" if obj.invoice_requested else "no"
        sent = "yes" if obj.invoice_sent else "no"
        return format_html(
            '<span class="text-nowrap">'
            f'<img src="/static/admin/img/icon-{requested}.svg" title="Invoice requested: {requested}">'
            " / "
            f'<img src="/static/admin/img/icon-{sent}.svg" title="Invoice sent: {sent}">'
            "<span>"
        )

    def visa(self, obj):
        requested = "yes" if obj.visa_requested else "no"
        sent = "yes" if obj.visa_sent else "no"
        return format_html(
            '<span class="text-nowrap">'
            f'<img src="/static/admin/img/icon-{requested}.svg" title="Visa requested: {requested}">'
            " / "
            f'<img src="/static/admin/img/icon-{sent}.svg" title="Visa sent: {sent}">'
            "</span>"
        )

    def with_coupon(self, obj):
        return obj.coupon is not None

    """
    Actions
    """

    def send_delegated_payment(self, request, queryset):
        DelegatedPaymentEmail(queryset=queryset).send()
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    def send_payment_reminder(self, request, queryset):
        PaymentReminderEmail(queryset=queryset).send()
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    def send_profile_reminder(self, request, queryset):
        RegistrationProfileReminderEmail(queryset=queryset).send()
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    def send_reminder(self, request, queryset):
        RegistrationReminderEmail(queryset=queryset).send()
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    def send_visa_reminder(self, request, queryset):
        VisaReminderEmail(queryset=queryset).send()
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    accepted_col.boolean = True
    accepted_col.short_description = "Accepted"
    paid_col.boolean = True
    paid_col.short_description = "Paid"
    with_coupon.boolean = True
    with_coupon.short_description = "Coupon"
    send_delegated_payment.short_description = "[Mailer] Send delegated payment link to users"
    send_payment_reminder.short_description = "[Mailer] Send payment reminder to users"
    send_profile_reminder.short_description = "[Mailer] Send profile reminder to users"
    send_reminder.short_description = "[Mailer] Send general reminder to users"
    send_visa_reminder.short_description = "[Mailer] Send visa reminder to users"
