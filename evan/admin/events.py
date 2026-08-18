from django import forms
from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from evan.models import Event, Fee, Sponsor

from .rel.files import FilesInline
from .rel.links import LinksInline
from .rel.permissions import PermissionsInline


class FeesInline(admin.TabularInline):
    model = Fee
    classes = ("collapse",)
    extra = 0


class SponsorsInline(admin.TabularInline):
    model = Sponsor
    classes = ("collapse",)
    extra = 0


class EventAdminForm(forms.ModelForm):
    """Admin form for Event with explicit fields for nested JSON config."""

    # extra_data: sponsor tiers
    sponsor_types = forms.CharField(
        required=False,
        label="Sponsor tiers",
        help_text="Comma-separated list ordered from highest to lowest tier, e.g. Platinum, Gold, Silver, Bronze",
        widget=forms.TextInput(attrs={"size": 60}),
    )

    # config: active modules
    module_abstracts = forms.BooleanField(required=False, label="Module: Abstracts")
    module_cms = forms.BooleanField(required=False, label="Module: CMS")
    module_subsessions = forms.BooleanField(required=False, label="Module: Subsessions")

    # config: payments (UGent bridge — the only type currently used)
    payments_type = forms.ChoiceField(
        required=False,
        choices=[("", "— disabled —"), ("ugent", "UGent bridge"), ("stripe", "Stripe")],
        label="Payment provider",
    )
    payments_wbs_element = forms.CharField(required=False, label="WBS element")
    payments_salt = forms.CharField(required=False, label="Salt IN/OUT", widget=forms.PasswordInput(render_value=True))
    payments_activation_date = forms.DateField(
        required=False, label="Activation date", widget=forms.DateInput(attrs={"type": "date"})
    )
    payments_test_mode = forms.BooleanField(required=False, label="Test mode")
    payments_allow_invoices = forms.BooleanField(required=False, label="Allow invoices", initial=True)

    class Meta:
        model = Event
        fields = [
            "is_virtual",
            "code",
            "name",
            "full_name",
            "city",
            "country",
            "presentation",
            "website",
            "hashtag",
            "start_date",
            "end_date",
            "registration_start_date",
            "registration_early_deadline",
            "registration_deadline",
            "registration_onsite_deadline",
            "social_event_bundle_fee",
            "signature",
            "email",
            "config",
            "registration_config",
            "extra_data",
            "custom_fields",
            "registrations_count",
            "accept_by_default",
        ]

    def __init__(self, *args, **kwargs):
        """Pre-populate virtual fields from the JSON columns."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            extra_data = self.instance.extra_data or {}
            self.fields["sponsor_types"].initial = ", ".join(extra_data.get("sponsor_types", []))

            config = self.instance.config or {}
            modules = config.get("active_modules", {})
            self.fields["module_abstracts"].initial = modules.get("abstracts", False)
            self.fields["module_cms"].initial = modules.get("cms", False)
            self.fields["module_subsessions"].initial = modules.get("subsessions", False)

            payments = config.get("payments") or {}
            self.fields["payments_type"].initial = payments.get("type", "")
            self.fields["payments_wbs_element"].initial = payments.get("wbs_element", "")
            self.fields["payments_salt"].initial = payments.get("salt", "")
            self.fields["payments_activation_date"].initial = payments.get("activation_date")
            self.fields["payments_test_mode"].initial = payments.get("test_mode", False)
            self.fields["payments_allow_invoices"].initial = payments.get("allow_invoices", True)

    def save(self, commit: bool = True):
        """Write virtual fields back into the JSON columns before saving."""
        instance = super().save(commit=False)

        # extra_data: sponsor_types
        raw = self.cleaned_data.get("sponsor_types", "")
        types = [t.strip() for t in raw.split(",") if t.strip()]
        extra_data = dict(instance.extra_data or {})
        extra_data["sponsor_types"] = types
        instance.extra_data = extra_data

        # config: active_modules
        config = dict(instance.config or {})
        config["active_modules"] = {
            "abstracts": self.cleaned_data.get("module_abstracts", False),
            "cms": self.cleaned_data.get("module_cms", False),
            "subsessions": self.cleaned_data.get("module_subsessions", False),
        }

        # config: payments
        payments_type = self.cleaned_data.get("payments_type", "")
        if payments_type:
            payments: dict = {"type": payments_type}
            if payments_type == "ugent":
                payments["wbs_element"] = self.cleaned_data.get("payments_wbs_element", "")
                payments["salt"] = self.cleaned_data.get("payments_salt", "")
                if self.cleaned_data.get("payments_activation_date"):
                    payments["activation_date"] = str(self.cleaned_data["payments_activation_date"])
                payments["test_mode"] = self.cleaned_data.get("payments_test_mode", False)
                payments["allow_invoices"] = self.cleaned_data.get("payments_allow_invoices", True)
            config["payments"] = payments
        else:
            config.pop("payments", None)

        instance.config = config

        if commit:
            instance.save()
        return instance


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin view for events."""

    form = EventAdminForm
    actions = ["registrations_excel"]
    date_hierarchy = "start_date"
    list_display = (
        "code",
        "start_date",
        "end_date",
        "name",
        "sessions_link",
        "registrations_link",
        "is_active",
        "is_open",
    )
    list_per_page = 30
    search_fields = ["city", "country", "start_date__year"]
    readonly_fields = ["registrations_count"]
    inlines = (
        FeesInline,
        SponsorsInline,
        LinksInline,
        PermissionsInline,
        FilesInline,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "code",
                    "name",
                    "full_name",
                    ("city", "country"),
                    ("start_date", "end_date"),
                    "website",
                    "hashtag",
                    "email",
                    "presentation",
                    "signature",
                )
            },
        ),
        (
            "Registration",
            {
                "classes": ("collapse",),
                "fields": (
                    ("registration_start_date", "registration_early_deadline"),
                    ("registration_deadline", "registration_onsite_deadline"),
                    "registrations_count",
                    "accept_by_default",
                    "is_virtual",
                    "social_event_bundle_fee",
                ),
            },
        ),
        (
            "Sponsor tiers",
            {
                "classes": ("collapse",),
                "description": "Ordered from highest to lowest (index = level value used on each sponsor).",
                "fields": ("sponsor_types",),
            },
        ),
        (
            "Active modules",
            {
                "classes": ("collapse",),
                "fields": ("module_abstracts", "module_cms", "module_subsessions"),
            },
        ),
        (
            "Payments",
            {
                "classes": ("collapse",),
                "fields": (
                    "payments_type",
                    "payments_wbs_element",
                    "payments_salt",
                    ("payments_activation_date", "payments_test_mode"),
                    "payments_allow_invoices",
                ),
            },
        ),
        (
            "Raw JSON (read-only for staff)",
            {
                "classes": ("collapse",),
                "fields": ("config", "extra_data", "registration_config"),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Superusers can edit raw JSON; everyone else sees it read-only."""
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly += ["config", "extra_data", "registration_config"]
        return readonly

    def get_queryset(self, request):
        qs = super().get_queryset(request).annotate(Count("sessions", distinct=True))
        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():  # type: ignore
            return qs
        if request.user.groups.filter(name="Administration").exists():  # type: ignore
            return qs.filter(acl__user_id__exact=request.user.id)  # type: ignore
        return qs.none()

    # custom actions

    @admin.action(description="🔡 Registrations overview")
    def registrations_excel(self, request, queryset):
        """Export registrations to Excel."""
        if queryset.count() != 1:
            self.message_user(request, "Please select only one event.", level="error")
            return None

        event = queryset.first()

        return HttpResponseRedirect(
            reverse("event:event_excel", kwargs={"code": event.code, "file_code": "registrations"})
        )

    # custom fields

    @admin.display(description="Active", boolean=True)
    def is_active(self, obj) -> bool:
        return obj.is_active

    @admin.display(description="Open", boolean=True)
    def is_open(self, obj) -> bool:
        return obj.is_open_for_registration

    @admin.display(description="Registrations")
    def registrations_link(self, obj):
        if obj.registrations_count == 0:
            return "-"
        url = reverse("admin:evan_registration_changelist")
        return format_html('<a href="{}?event__id__exact={}">{}</a>', url, obj.id, obj.registrations_count)

    @admin.display(description="Sessions")
    def sessions_link(self, obj):
        if obj.sessions__count == 0:
            return "-"
        url = reverse("admin:evan_session_changelist")
        return format_html('<a href="{}?event__id__exact={}">{}</a>', url, obj.id, obj.sessions__count)
