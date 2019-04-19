from django.contrib import admin

from evan.models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return False
