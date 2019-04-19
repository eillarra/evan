from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from evan.models import Registration, InvitationLetter


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
    search_fields = ('id', 'user__email', 'user__username', 'user__first_name', 'user__last_name')

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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user__profile', 'coupon').prefetch_related('event')

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
