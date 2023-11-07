from django.contrib import admin

from evan.models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "value", "event", "notes")
    list_filter = (("event", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("code", "notes")

    def has_module_permission(self, request):
        return False
