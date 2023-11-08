import os

from django.conf import settings
from django.middleware.csrf import get_token as get_csrf_token
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.generic import View
from inertia import render

from evan.api.serializers.users import UserSerializer


def active_path(request, patterns) -> bool:
    if patterns:
        for pattern in patterns.split(","):
            try:
                if pattern == request.resolver_match.url_name:
                    return True
            except Exception:
                return False
    return False


def render_inertia(request, vue_entry_point: str, *, props: dict | None = None, page_title: str | None = None):
    """
    Render a Vue component with Inertia.
    It adds some basic props that can be helpful.
    """

    return render(
        request,
        slugify(vue_entry_point),
        props={
            "django_csrf_token": get_csrf_token(request),
            "django_debug": settings.DEBUG,
            "django_env": os.environ.get("DJANGO_ENV", "development"),
            "django_locale": request.LANGUAGE_CODE,
            "django_user": UserSerializer(request.user, context={"request": request}).data
            if request.user.is_authenticated
            else None,
            "git_commit_hash": os.environ.get("GIT_REV", None),
            "sentry_vue_dsn": os.environ.get("SENTRY_VUE_DSN", None),
            "evan_menu": [],
            "vue_template": "light",
        }
        | (props or {}),
        template_data={
            "page_title": page_title or "Evan",
            "vue_entry_point": vue_entry_point,
        },
    )


class CachedInertiaView(View):
    page_title: str | None = None
    vue_entry_point: str

    def get_page_title(self, request, *args, **kwargs) -> str | None:
        return f"{self.page_title} - Evan" if self.page_title and self.page_title != "Evan" else None

    def get_props(self, request, *args, **kwargs) -> dict:
        return {}

    def get(self, request, *args, **kwargs):
        if self.vue_entry_point is None:
            raise NotImplementedError("`vue_entry_point` must be set")

        return render_inertia(
            request,
            self.vue_entry_point,
            props=self.get_props(request, *args, **kwargs),
            page_title=self.get_page_title(self, request, *args, **kwargs),
        )


class InertiaView(CachedInertiaView):
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
