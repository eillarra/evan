from rest_framework.renderers import BrowsableAPIRenderer


class NoFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    We don't want the HTML forms and filters to be rendered in the browsable API.
    It can be very slow when there are lots of entries in related fiels.
    The browsable API is only used in DEBUG mode anyway, so it only affects development.
    """

    def get_rendered_html_form(self, *args, **kwargs):
        return

    def get_filter_form(self, data, view, request):
        return
