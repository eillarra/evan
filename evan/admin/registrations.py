from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.urls import path, reverse
from django.utils.html import format_html

from evan.models import InvitationLetter, Registration
from evan.services.mailer.registrations import schedule_registration_email


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
    search_fields = (
        "id",
        "uuid",
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__affiliation",
    )
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
        "mark_as_accepted",
        "regenerate_payment_hash",
        "send_reminder",
        "send_visa_reminder",
        "send_payment_reminder",
        "send_delegated_payment",
        "send_profile_reminder",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user", "coupon").prefetch_related("event")
        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():  # type: ignore
            return qs
        if request.user.groups.filter(name="Administration").exists():  # type: ignore
            return qs.filter(event__acl__user_id__exact=request.user.id)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:  # type: ignore
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
        if obj is None:
            self.message_user(request, "The requested registration does not exist.", level="error")
            return None
        maker = InvitationLetterPdfMaker(registration=obj, filename=f"letter--{obj.uuid}.pdf", as_attachment=False)
        return maker.response

    def name(self, obj):
        affiliation = obj.user.affiliation if obj.user.affiliation else "-"
        url = reverse("admin:evan_user_changelist")
        return format_html(f'<a href="{url}{obj.user_id}/" target="admin_user">{obj.user.name}</a>, {affiliation}')

    # custom actions

    @admin.action(description="[Bulk] Mark registrations as accepted")
    def mark_as_accepted(self, request, queryset):
        queryset.update(is_accepted=True)
        admin.ModelAdmin.message_user(self, request, "Registrations are marked as accepted.")

    @admin.action(description="[Bulk] Regenerate payment hash")
    def regenerate_payment_hash(self, request, queryset):
        queryset.update(unique_hash="")
        for registration in queryset:
            registration.unique_hash = registration.generate_unique_hash()
            registration.save()
        admin.ModelAdmin.message_user(self, request, "Payment hashes are regenerated.")

    @admin.action(description="[Mailer] Send delegated payment link to users")
    def send_delegated_payment(self, request, queryset):
        queryset = queryset.filter(is_accepted=True, saldo__lt=0, invoice_requested=False)
        for registration in queryset:
            schedule_registration_email(registration, code="registration.payment_delegated")
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    @admin.action(description="[Mailer] Send payment reminder to users")
    def send_payment_reminder(self, request, queryset):
        queryset = queryset.filter(is_accepted=True, saldo__lt=0)
        for registration in queryset:
            schedule_registration_email(registration, code="registration.payment_reminder")
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    @admin.action(description="[Mailer] Send profile reminder to users")
    def send_profile_reminder(self, request, queryset):
        for registration in queryset:
            schedule_registration_email(registration, code="registration.profile_reminder")
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    @admin.action(description="[Mailer] Send initial registration email to users")
    def send_reminder(self, request, queryset):
        for registration in queryset:
            schedule_registration_email(registration, code="registration.created")
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    @admin.action(description="[Mailer] Send visa reminder to users")
    def send_visa_reminder(self, request, queryset):
        queryset = queryset.filter(is_accepted=True, visa_requested=True, visa_sent=False)
        for registration in queryset:
            schedule_registration_email(registration, code="registration.visa_reminder")
        admin.ModelAdmin.message_user(self, request, "Emails are being sent.")

    # custom fields

    @admin.display(description="Accepted", boolean=True)
    def accepted_col(self, obj) -> bool:
        return obj.is_accepted

    def fee(self, obj):
        return format_html(f"{obj.base_fee}&nbsp;+&nbsp;{obj.extra_fees + obj.manual_extra_fees}")

    @admin.display(description="Paid", boolean=True)
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

    @admin.display(description="Coupon", boolean=True)
    def with_coupon(self, obj):
        return obj.coupon is not None
