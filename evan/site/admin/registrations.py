from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.urls import path, reverse
from django.utils.html import format_html

from evan.models import Registration, InvitationLetter
from evan.site.emails.registrations import RegistrationReminderEmail, PaymentReminderEmail, VisaReminderEmail


class RegistrationIsPaidFilter(admin.SimpleListFilter):
    title = 'payment status'
    parameter_name = 'paid'

    def lookups(self, request, model_admin):
        return (
            ('y', 'Paid'),
            ('c', 'Paid, using a coupon'),
            ('n', 'Not paid, no invoice'),
            ('i', 'Not paid, but requested invoice'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'y':
            return queryset.filter(saldo__gte=0)
        elif self.value() == 'c':
            return queryset.filter(saldo__gte=0, coupon__isnull=False)
        elif self.value() == 'n':
            return queryset.filter(saldo__lt=0, invoice_requested=False)
        elif self.value() == 'i':
            return queryset.filter(saldo__lt=0, invoice_requested=True)


class InvitationLetterInline(admin.StackedInline):
    model = InvitationLetter
    fk_name = 'registration'
    extra = 0
    verbose_name = 'Invitation letter'
    verbose_name_plural = 'Invitation letter'


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'created_at', 'name', 'fee', 'is_paid', 'with_coupon', 'invoice_requested', 'invoice_sent',
                    'visa_requested', 'visa_sent')
    list_filter = (RegistrationIsPaidFilter, 'invoice_requested', 'invoice_sent',
                   'visa_requested', 'visa_sent', 'event')
    search_fields = ('id', 'uuid', 'user__email', 'user__username', 'user__first_name', 'user__last_name')

    raw_id_fields = ('event', 'user', 'coupon')
    readonly_fields = ('event', 'base_fee', 'extra_fees', 'paid', 'saldo')
    fieldsets = (
        (None, {
            'fields': ('event', 'user'),
        }),
        ('PAYMENT', {
            'fields': ('fee_type', ('base_fee', 'extra_fees'), 'manual_extra_fees',
                       ('paid_via_invoice', 'invoice_requested', 'invoice_sent'),
                       'coupon', 'paid', 'saldo'),
        }),
        ('EXTRA INFORMATION', {
            'fields': ('visa_requested', 'visa_sent'),
        }),
    )
    inlines = (InvitationLetterInline,)
    actions = ('send_reminder', 'send_visa_reminder', 'send_payment_reminder')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user__profile', 'coupon').prefetch_related('event')

    def get_urls(self):
        my_urls = [
            path('<path:object_id>/letter/', self.pdf_letter_view, name='registration_pdf_letter'),
        ]
        return my_urls + super().get_urls()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        extra_context = extra_context or {}
        extra_context['has_letter'] = InvitationLetter.objects.filter(registration_id=object_id).exists()
        extra_context['receipt_url'] = obj.get_receipt_url() if obj.paid else None
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def pdf_letter_view(self, request, object_id, extra_context=None):
        from evan.site.pdfs.registrations import InvitationLetterPdfMaker
        obj = self.get_object(request, unquote(object_id))
        maker = InvitationLetterPdfMaker(registration=obj, filename=f'letter--{obj.uuid}.pdf', as_attachment=False)
        return maker.response

    def name(self, obj):
        affiliation = obj.user.profile.affiliation if obj.user.profile.affiliation else '-'
        url = reverse('admin:auth_user_changelist')
        return format_html(
            f'<a href="{url}{obj.user_id}/" target="admin_user">{obj.user.profile.name}</a>, {affiliation}'
        )

    def fee(self, obj):
        return format_html(f'{obj.base_fee}&nbsp;+&nbsp;{obj.extra_fees}')

    def is_paid(self, obj) -> bool:
        return obj.is_paid
    is_paid.boolean = True
    is_paid.short_description = 'Paid'

    def with_coupon(self, obj):
        return obj.coupon is not None
    with_coupon.boolean = True
    with_coupon.short_description = 'Coupon'

    def send_reminder(self, request, queryset):
        for instance in queryset:
            RegistrationReminderEmail(instance=instance).send()
        admin.ModelAdmin.message_user(self, request, 'Emails are being sent.')
    send_reminder.short_description = ('[Mailer] Send general reminder to users')

    def send_payment_reminder(self, request, queryset):
        for instance in queryset:
            PaymentReminderEmail(instance=instance).send()
        admin.ModelAdmin.message_user(self, request, 'Emails are being sent.')
    send_payment_reminder.short_description = ('[Mailer] Send payment reminder to users')

    def send_visa_reminder(self, request, queryset):
        for instance in queryset:
            VisaReminderEmail(instance=instance).send()
        admin.ModelAdmin.message_user(self, request, 'Emails are being sent.')
    send_visa_reminder.short_description = ('[Mailer] Send visa reminder to users')
