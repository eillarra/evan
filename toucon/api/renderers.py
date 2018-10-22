from rest_framework.renderers import BrowsableAPIRenderer


class NoFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    We don't want the HTML forms and filters to be rendered in the browsable API.
    It can be very slow for Porras for example, where the view tries to load all Dorsals.
    The browsable API is only used in DEBUG mode anyway, so it only affects development.
    """

    def get_rendered_html_form(self, *args, **kwargs):
        return

    def get_filter_form(self, data, view, request):
        return
